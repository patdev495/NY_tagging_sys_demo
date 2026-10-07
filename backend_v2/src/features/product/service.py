from typing import Any

from fastapi import HTTPException
from pydantic import ValidationError
from sqlalchemy import func, or_
from sqlalchemy.orm import Session, joinedload

from src.core.models import Carton, Customer, Product, ProductInternalFactoryPartNumber
from src.features.carton.sn_allocator import plan_next_carton_sn

from . import schemas


def normalize_internal_factory_part_number(value: Any) -> str:
    return (str(value) if value is not None else "").strip().upper()


def _validate_erro_internal_factory_part_number(db: Session, product: Product, *, required: bool = False) -> None:
    customer = db.query(Customer).filter(Customer.id == product.customer_id).first()
    if not customer or getattr(customer, "code", None) != "ERRO":
        return

    normalized_value = normalize_internal_factory_part_number(product.internal_factory_part_number)
    if not normalized_value:
        if required:
            raise HTTPException(status_code=422, detail="Product Erro requires internal_factory_part_number.")
        return

    product.internal_factory_part_number = normalized_value  # type: ignore

    # Check mapping table and product table for duplicates across other products
    existing_mapping = (
        db.query(ProductInternalFactoryPartNumber)
        .filter(
            ProductInternalFactoryPartNumber.customer_id == product.customer_id,
            func.upper(ProductInternalFactoryPartNumber.internal_factory_part_number) == normalized_value,
            ProductInternalFactoryPartNumber.product_id != product.id,
        )
        .first()
    )
    if existing_mapping:
        raise HTTPException(status_code=409, detail="Factory P/N đã được gán cho một Product Erro khác.")

    duplicate = (
        db.query(Product)
        .filter(
            Product.customer_id == product.customer_id,
            func.upper(Product.internal_factory_part_number) == normalized_value,
            Product.id != product.id,
        )
        .first()
    )
    if duplicate:
        raise HTTPException(status_code=409, detail="Factory P/N đã được gán cho một Product Erro khác.")


def get_all_products(db: Session, customer_code: str | None = None, search: str | None = None):
    query = db.query(Product).options(joinedload(Product.internal_factory_part_numbers))
    if customer_code:
        query = query.join(Customer).filter(Customer.code == customer_code)
    if search:
        search_filter = f"%{search}%"
        query = query.outerjoin(Product.internal_factory_part_numbers).filter(
            or_(
                Product.item_name.ilike(search_filter),
                Product.asin.ilike(search_filter),
                Product.mfr_pn.ilike(search_filter),
                Product.product_desc.ilike(search_filter),
                Product.internal_factory_part_number.ilike(search_filter),
                Product.factory_item_code.ilike(search_filter),
                ProductInternalFactoryPartNumber.internal_factory_part_number.ilike(search_filter),
            )
        ).distinct()
    return query.all()


def get_products_by_customer(customer_id: int, db: Session):
    return (
        db.query(Product)
        .options(joinedload(Product.internal_factory_part_numbers))
        .filter(Product.customer_id == customer_id)
        .all()
    )


def get_product_by_id(product_id: int, db: Session):
    return (
        db.query(Product)
        .options(joinedload(Product.internal_factory_part_numbers))
        .filter(Product.id == product_id)
        .first()
    )


def resolve_erro_product_by_internal_factory_part_number(value: str, db: Session):
    normalized_value = normalize_internal_factory_part_number(value)
    if not normalized_value:
        return None

    # 1. First lookup via the 1-N mapping table product_internal_factory_part_numbers
    mappings = (
        db.query(ProductInternalFactoryPartNumber)
        .join(Customer, ProductInternalFactoryPartNumber.customer_id == Customer.id)
        .join(Product, ProductInternalFactoryPartNumber.product_id == Product.id)
        .filter(
            Customer.code == "ERRO",
            func.upper(ProductInternalFactoryPartNumber.internal_factory_part_number) == normalized_value,
        )
        .limit(2)
        .all()
    )

    if len(mappings) > 1:
        raise HTTPException(status_code=409, detail="Factory P/N được gán cho nhiều Product Erro.")

    if len(mappings) == 1:
        product = mappings[0].product
        product.internal_factory_part_number = normalized_value  # type: ignore
        return product

    # 2. Backward-compatible fallback to legacy column if mapping row does not exist
    legacy_products = (
        db.query(Product)
        .join(Customer, Product.customer_id == Customer.id)
        .filter(
            Customer.code == "ERRO",
            func.upper(Product.internal_factory_part_number) == normalized_value,
        )
        .limit(2)
        .all()
    )
    if len(legacy_products) > 1:
        raise HTTPException(status_code=409, detail="Factory P/N được gán cho nhiều Product Erro.")
    if len(legacy_products) == 1:
        product = legacy_products[0]
        product.internal_factory_part_number = normalized_value  # type: ignore
        return product

    return None


def get_product_factory_part_numbers(product_id: int, db: Session) -> list[ProductInternalFactoryPartNumber]:
    return (
        db.query(ProductInternalFactoryPartNumber)
        .filter(ProductInternalFactoryPartNumber.product_id == product_id)
        .order_by(ProductInternalFactoryPartNumber.id.asc())
        .all()
    )


def add_product_factory_part_number(
    product_id: int,
    data: schemas.InternalFactoryPartNumberCreate,
    db: Session,
) -> ProductInternalFactoryPartNumber:
    product = get_product_by_id(product_id, db)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    normalized_code = normalize_internal_factory_part_number(data.internal_factory_part_number)
    drawing_code = (data.source_drawing_code or "").strip().upper()

    existing = (
        db.query(ProductInternalFactoryPartNumber)
        .filter(
            ProductInternalFactoryPartNumber.customer_id == product.customer_id,
            func.upper(ProductInternalFactoryPartNumber.internal_factory_part_number) == normalized_code,
        )
        .first()
    )
    if existing:
        if getattr(existing, "product_id", None) == product_id:
            raise HTTPException(status_code=409, detail="Factory P/N đã tồn tại cho Product này.")
        raise HTTPException(status_code=409, detail="Factory P/N đã được gán cho một Product Erro khác.")

    mapping = ProductInternalFactoryPartNumber(
        product_id=product.id,
        customer_id=product.customer_id,
        internal_factory_part_number=normalized_code,
        source_drawing_code=drawing_code,
    )
    db.add(mapping)
    db.commit()
    db.refresh(mapping)
    return mapping


def batch_add_product_factory_part_numbers(
    product_id: int,
    items: list[schemas.InternalFactoryPartNumberCreate],
    db: Session,
) -> list[ProductInternalFactoryPartNumber]:
    product = get_product_by_id(product_id, db)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    created = []
    for item in items:
        normalized_code = normalize_internal_factory_part_number(item.internal_factory_part_number)
        drawing_code = (item.source_drawing_code or "").strip().upper()

        existing = (
            db.query(ProductInternalFactoryPartNumber)
            .filter(
                ProductInternalFactoryPartNumber.customer_id == product.customer_id,
                func.upper(ProductInternalFactoryPartNumber.internal_factory_part_number) == normalized_code,
            )
            .first()
        )
        if existing:
            if getattr(existing, "product_id", None) != product_id:
                raise HTTPException(status_code=409, detail=f"Factory P/N {normalized_code} đã được gán cho Product khác.")
            continue

        mapping = ProductInternalFactoryPartNumber(
            product_id=product.id,
            customer_id=product.customer_id,
            internal_factory_part_number=normalized_code,
            source_drawing_code=drawing_code,
        )
        db.add(mapping)
        created.append(mapping)

    db.commit()
    for m in created:
        db.refresh(m)
    return created


def delete_product_factory_part_number(
    product_id: int,
    mapping_id: int,
    db: Session,
) -> bool:
    mapping = (
        db.query(ProductInternalFactoryPartNumber)
        .filter(
            ProductInternalFactoryPartNumber.id == mapping_id,
            ProductInternalFactoryPartNumber.product_id == product_id,
        )
        .first()
    )
    if not mapping:
        raise HTTPException(status_code=404, detail="Mapping not found")

    db.delete(mapping)
    db.commit()
    return True


def create_product(db: Session, product: schemas.ProductCreate):
    db_product = Product(**product.model_dump())
    _validate_erro_internal_factory_part_number(db, db_product, required=False)
    db.add(db_product)
    db.flush()

    # If an internal_factory_part_number was provided upon creation, sync it into mapping table
    if getattr(db_product, "internal_factory_part_number", None):
        norm = normalize_internal_factory_part_number(db_product.internal_factory_part_number)
        customer = db.query(Customer).filter(Customer.id == db_product.customer_id).first()
        if customer and getattr(customer, "code", None) == "ERRO":
            mapping = ProductInternalFactoryPartNumber(
                product_id=db_product.id,
                customer_id=customer.id,
                internal_factory_part_number=norm,
                source_drawing_code="LEGACY",
            )
            db.add(mapping)

    db.commit()
    db.refresh(db_product)
    return db_product


def update_product(db: Session, product_id: int, product: schemas.ProductUpdate):
    db_product = get_product_by_id(product_id, db)
    if not db_product:
        return None

    update_data = product.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_product, key, value)

    _validate_erro_internal_factory_part_number(
        db,
        db_product,
        required=False,
    )

    if "internal_factory_part_number" in update_data and getattr(db_product, "internal_factory_part_number", None):
        norm = normalize_internal_factory_part_number(db_product.internal_factory_part_number)
        customer = db.query(Customer).filter(Customer.id == db_product.customer_id).first()
        if customer and getattr(customer, "code", None) == "ERRO":
            existing = (
                db.query(ProductInternalFactoryPartNumber)
                .filter(
                    ProductInternalFactoryPartNumber.customer_id == customer.id,
                    func.upper(ProductInternalFactoryPartNumber.internal_factory_part_number) == norm,
                )
                .first()
            )
            if not existing:
                db.add(ProductInternalFactoryPartNumber(
                    product_id=db_product.id,
                    customer_id=customer.id,
                    internal_factory_part_number=norm,
                    source_drawing_code="LEGACY",
                ))

    if db_product.template_type == "erro_04":
        try:
            schemas.ProductCreate.model_validate({
                "customer_id": db_product.customer_id,
                "item_name": db_product.item_name,
                "upc": db_product.upc,
                "packed_qty": db_product.packed_qty,
                "template_type": db_product.template_type,
                "template_path": db_product.template_path,
                "packing_mode": db_product.packing_mode,
                "target_weight": db_product.target_weight,
                "min_weight": db_product.min_weight,
                "max_weight": db_product.max_weight,
                "weight_unit": db_product.weight_unit,
                "mfr_pn": db_product.mfr_pn,
                "revision": db_product.revision,
                "product_desc": db_product.product_desc,
                "factory_item_code": db_product.factory_item_code,
                "carton_id_prefix": db_product.carton_id_prefix,
            })
        except ValidationError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc

    if db_product.template_type == "erro_03":
        try:
            schemas.ProductCreate.model_validate({
                "customer_id": db_product.customer_id,
                "item_name": db_product.item_name,
                "packed_qty": db_product.packed_qty,
                "template_type": db_product.template_type,
                "template_path": db_product.template_path,
                "packing_mode": db_product.packing_mode,
                "customer_project": db_product.customer_project,
                "production_stage": db_product.production_stage,
                "luxshare_part_number": db_product.luxshare_part_number,
            })
        except ValidationError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc

    db.commit()
    db.refresh(db_product)
    return db_product


def delete_product(db: Session, product_id: int):
    db_product = get_product_by_id(product_id, db)
    if not db_product:
        return False

    db.delete(db_product)
    db.commit()
    return True


def get_next_sn(product_id: int, db: Session, yymm: str | None = None):
    product = get_product_by_id(product_id, db)
    if not product:
        return {"next_seq": 1, "next_sn": None, "prefix": ""}

    if product.template_type == "erro_02":
        from src.features.carton.sscc_allocator import plan_next_sscc_carton_sn
        plan = plan_next_sscc_carton_sn(db, product)
        return {
            "next_seq": plan.sequence,
            "next_sn": plan.carton_sn,
            "prefix": f"0{plan.company_prefix}",
            "sscc_text": plan.sscc_text,
            "check_digit": plan.check_digit,
        }

    if product.template_type == "erro_03":
        from src.features.carton.erro_03_sn_allocator import plan_next_erro_03_carton_sn
        plan = plan_next_erro_03_carton_sn(db, product)
        return {
            "next_seq": plan.sequence,
            "next_sn": plan.carton_sn,
            "supplier_code": plan.supplier_code,
            "yymmdd": plan.yymmdd,
        }

    if product.template_type == "erro_04":
        from src.features.carton.erro_04_sn_allocator import plan_next_erro_04_carton_sn
        plan = plan_next_erro_04_carton_sn(db, product)
        return {
            "next_seq": plan.sequence,
            "next_sn": plan.carton_sn,
            "carton_id_prefix": plan.carton_id_prefix,
            "date_code": plan.date_code,
        }

    if product.template_type == "erro_05":
        from src.features.carton.erro_05_sn_allocator import plan_next_erro_05_carton_sn
        plan = plan_next_erro_05_carton_sn(db, product)
        return {
            "next_seq": plan.sequence,
            "next_sn": plan.carton_sn,
            "pkg_prefix": plan.pkg_prefix,
            "date_code": plan.date_code,
        }

    if product.packing_mode == "weight_scale" or product.template_type == "erro_01":
        from src.features.carton.erro_01_sn_allocator import plan_next_erro_01_carton_sn
        plan = plan_next_erro_01_carton_sn(db, product, custom_yymm=yymm)
        return {"next_seq": plan.sequence, "next_sn": plan.carton_sn, "prefix": plan.prefix, "yymm": plan.yymm}

    plan = plan_next_carton_sn(db, product, custom_yymm=yymm, include_slots=True)
    return {"next_seq": plan.sequence, "next_sn": plan.carton_sn, "prefix": plan.prefix}



def get_last_carton(product_id: int, db: Session, job_order: str | None = None):
    query = db.query(Carton).options(joinedload(Carton.items)).filter(
        Carton.product_id == product_id,
        Carton.status.in_(["SUCCESS", "PRINTED"]),
        Carton.is_reprint == 0,
    )
    if job_order:
        query = query.filter(Carton.job_order == job_order)
    carton = query.order_by(Carton.id.desc()).first()

    if carton:
        items = getattr(carton, "items", None)
        carton.items_count = len(items) if isinstance(items, (list, tuple)) else 0

    return carton
