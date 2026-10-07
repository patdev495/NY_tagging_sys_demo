import logging
import math
import os
from datetime import datetime
from typing import cast

from fastapi import HTTPException
from sqlalchemy import func, text
from sqlalchemy.orm import Session

from src.core import models
from src.features.carton.sn_allocator import plan_job_order_slots
from src.features.job_order import schemas

logger = logging.getLogger("JobOrderService")

def get_job_order_from_erp(db: Session, job_order: str, customer_filter: str | None = None):
    """
    Query the Job Order details from the Linked Server 192.168.206.18.
    If database engine is SQLite or if query fails due to database driver / connection issues,
    it falls back to a simulated mock response for local testing/development.
    """
    try:
        is_sqlite = db.get_bind().dialect.name == "sqlite"
    except Exception:
        is_sqlite = False
        
    from src.core.config import settings
    is_demo = (
        os.environ.get("DEMO_MODE", "").lower() in ("true", "1", "yes")
        or getattr(settings, "DEMO_MODE", False) is True
        or is_sqlite
        or not getattr(settings, "DB_SERVER", "")
    )

    if is_demo:
        logger.info(f"Demo mode detected. Falling back to mock for Job Order '{job_order}' (filter: {customer_filter})")
        return get_mocked_job_order(db, job_order, customer_filter=customer_filter)

        
    query = text("""
        SELECT wadoco AS [工單], walitm AS [年益料號], wadl01 AS [客戶料號], wauorg/10000 AS [數量] 
        FROM [192.168.206.18].ShopFloorDW.DBO.F4801 
        WHERE wadoco = :job_order
    """)
    try:
        row = db.execute(query, {"job_order": job_order}).fetchone()
        if not row:
            if is_demo:
                return get_mocked_job_order(db, job_order, customer_filter=customer_filter)
            raise HTTPException(status_code=400, detail=f"Không tìm thấy công lệnh '{job_order}' trên hệ thống ShopFloorDW.")
            
        wadoco = str(row[0] or "").strip()
        walitm = str(row[1] or "").strip()
        wadl01 = str(row[2] or "").strip()
        try:
            qty = int(row[3])
        except Exception:
            qty = 0
            
        return {
            "job_order": wadoco,
            "product_code": walitm,
            "customer_ref": wadl01,
            "quantity": qty
        }
    except Exception as e:
        if is_demo:
            return get_mocked_job_order(db, job_order, customer_filter=customer_filter)
        if isinstance(e, HTTPException):
            raise e
        logger.error(f"Linked Server query failed: {e}. Raising HTTP error.")
        raise HTTPException(
            status_code=400, 
            detail=f"Không thể kết nối cơ sở dữ liệu ShopFloor hoặc công lệnh không hợp lệ. Chi tiết: {e!s}"
        )

def get_mocked_job_order(db: Session, job_order: str, customer_filter: str | None = None):
    """
    DEMO MODE: Returns simulated Job Order details from local SQLite products.
    Cycles through products based on the job_order string,
    so different job orders map to different products for a realistic demo.
    """
    # 1. If station is UI, choose products belonging to UI (non-ERRO)
    if customer_filter == "UI":
        ui_products = (
            db.query(models.Product)
            .join(models.Customer)
            .filter(models.Customer.code != "ERRO")
            .all()
        )
        if ui_products:
            idx = sum(ord(c) for c in job_order) % len(ui_products)
            product = ui_products[idx]
            return {
                "job_order": job_order,
                "product_code": product.item_name or "UI-PROD",
                "customer_ref": product.item_name or "UI-PROD",
                "quantity": 10 * (product.packed_qty or 1),
            }

    # 2. If station is ERRO (or default), choose ERRO products
    erro_products = (
        db.query(models.Product)
        .join(models.Customer)
        .filter(models.Customer.code == "ERRO")
        .all()
    )

    if erro_products:
        idx = sum(ord(c) for c in job_order) % len(erro_products)
        product = erro_products[idx]
        factory_pn = product.internal_factory_part_number or product.item_name or "UNKNOWN"
        return {
            "job_order": job_order,
            "product_code": factory_pn,
            "customer_ref": product.item_name or factory_pn,
            "quantity": 20 * (product.packed_qty or 1),
        }

    # 3. Fallback: any product
    product = db.query(models.Product).first()
    if not product:
        return {
            "job_order": job_order,
            "product_code": "DEMO-001",
            "customer_ref": "Demo Product",
            "quantity": 300,
        }

    return {
        "job_order": job_order,
        "product_code": product.internal_factory_part_number or product.item_name or "DEMO-001",
        "customer_ref": product.item_name or "Demo Product",
        "quantity": 15 * (product.packed_qty or 1),
    }


def find_matching_product(db: Session, customer_ref: str | None, product_code: str | None = None):
    """
    Search for a Product matching either the Customer Ref (wadl01) or Product Code (walitm).
    Supports matching typos like Path vs Patch.
    """
    clean_ref = (customer_ref or "").strip()
    clean_code = (product_code or "").strip()

    if not clean_ref:
        if clean_code:
            return db.query(models.Product).filter(
                (models.Product.internal_factory_part_number == clean_code) |
                (models.Product.item_name == clean_code)
            ).first()
        return None

    # 1. Match by item_name exactly
    product = db.query(models.Product).filter(models.Product.item_name == clean_ref).first()
    if product:
        return product
        
    # 2. Match by item_name case-insensitively
    product = db.query(models.Product).filter(func.lower(models.Product.item_name) == clean_ref.lower()).first()
    if product:
        return product
        
    # 3. Typo handling: Replace 'Patch' with 'Path' in the search ref
    if 'Patch' in clean_ref:
        path_ref = clean_ref.replace('Patch', 'Path')
        product = db.query(models.Product).filter(func.lower(models.Product.item_name) == path_ref.lower()).first()
        if product:
            return product
            
    # 4. Typo handling: Replace 'Path' with 'Patch' in the search ref
    if 'Path' in clean_ref:
        patch_ref = clean_ref.replace('Path', 'Patch')
        product = db.query(models.Product).filter(func.lower(models.Product.item_name) == patch_ref.lower()).first()
        if product:
            return product
            
    if clean_code:
        product = db.query(models.Product).filter(
            (models.Product.internal_factory_part_number == clean_code) |
            (models.Product.item_name == clean_code)
        ).first()
        if product:
            return product

    return None

def get_or_create_job_order_slots(db: Session, job_order: str):
    # 1. Fetch ERP Job Order details
    erp_data = get_job_order_from_erp(db, job_order, customer_filter="UI")
    
    # 2. Find matching product
    cust_ref = str(erp_data.get("customer_ref") or "").strip()
    prod_code = str(erp_data.get("product_code") or "").strip()
    product = find_matching_product(db, cust_ref, prod_code)

    from src.core.config import settings
    is_demo = (
        os.environ.get("DEMO_MODE", "").lower() in ("true", "1", "yes")
        or getattr(settings, "DEMO_MODE", False) is True
        or (db.get_bind().dialect.name == "sqlite")
        or not getattr(settings, "DB_SERVER", "")
    )

    if not product or (product.customer and product.customer.code.upper() == "ERRO"):
        if is_demo:
            ui_products = (
                db.query(models.Product)
                .join(models.Customer)
                .filter(models.Customer.code != "ERRO")
                .all()
            )
            if ui_products:
                idx = sum(ord(c) for c in job_order) % len(ui_products)
                product = ui_products[idx]

    if not product:
        ref_display = cust_ref or prod_code or job_order
        raise HTTPException(
            status_code=400, 
            detail=f"Không tìm thấy con hàng '{ref_display}' tương ứng trong cơ sở dữ liệu."
        )

    if not is_demo and product.customer and product.customer.code.upper() == "ERRO":
        raise HTTPException(
            status_code=400,
            detail="Công lệnh ERRO không cấp slot thùng. Vui lòng dùng trạm cân ERRO.",
        )
        
    # 3. Calculate total cartons
    packed_qty = cast(int, product.packed_qty) or 1
    if packed_qty <= 0:
        packed_qty = 1
        
    total_qty = int(erp_data.get("quantity") or (10 * packed_qty))
    total_cartons = math.ceil(total_qty / packed_qty)

    if total_cartons <= 0:
        total_cartons = 10
        total_qty = total_cartons * packed_qty
        
    # 4. Check if slots already exist
    existing_slots = db.query(models.JobOrderCartonSlot).filter(
        models.JobOrderCartonSlot.job_order == job_order
    ).order_by(models.JobOrderCartonSlot.carton_number).all()
    
    if existing_slots:
        return schemas.JobOrderDetailsResponse(
            job_order=job_order,
            total_qty=total_qty,
            total_cartons=total_cartons,
            product=schemas.JobOrderProductResponse.model_validate(product),
            slots=[schemas.JobOrderSlotResponse.model_validate(s) for s in existing_slots]
        )
        
    # 5. Allocate new slots
    sn_plans = plan_job_order_slots(db, product, total_cartons)
    slots = []
    for i, sn_plan in enumerate(sn_plans, start=1):
        slot = models.JobOrderCartonSlot(
            job_order=job_order,
            product_id=product.id,
            carton_number=i,
            carton_sn=sn_plan.carton_sn,
            status="PENDING"
        )
        db.add(slot)
        slots.append(slot)
        
    try:
        db.commit()
        for s in slots:
            db.refresh(s)
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Không thể lưu danh sách cấp phát thùng: {e!s}")
        
    return schemas.JobOrderDetailsResponse(
        job_order=job_order,
        total_qty=total_qty,
        total_cartons=total_cartons,
        product=schemas.JobOrderProductResponse.model_validate(product),
        slots=[schemas.JobOrderSlotResponse.model_validate(s) for s in slots]
    )

def get_job_order_slots_list(db: Session, job_order: str):
    slots = db.query(models.JobOrderCartonSlot).filter(
        models.JobOrderCartonSlot.job_order == job_order
    ).order_by(models.JobOrderCartonSlot.carton_number).all()
    
    return [schemas.JobOrderSlotResponse.model_validate(s) for s in slots]


def resolve_erro_job_order(db: Session, job_order: str) -> schemas.ErroJobOrderResolutionResponse:
    clean_job_order = job_order.strip()
    if not clean_job_order:
        raise HTTPException(status_code=400, detail="Mã công lệnh không được để trống.")

    from src.core.config import settings
    is_demo = (
        os.environ.get("DEMO_MODE", "").lower() in ("true", "1", "yes")
        or getattr(settings, "DEMO_MODE", False) is True
        or (db.get_bind().dialect.name == "sqlite")
        or not getattr(settings, "DB_SERVER", "")
    )

    # 1. Fetch ERP Job Order details
    erp_data = get_job_order_from_erp(db, clean_job_order, customer_filter="ERRO")
    factory_part_number = str(erp_data.get("product_code") or "").strip()
    customer_ref = str(erp_data.get("customer_ref") or "").strip()
    total_qty = int(erp_data.get("quantity") or 0)

    # 2. Resolve Erro product by internal factory part number
    from src.features.product.service import resolve_erro_product_by_internal_factory_part_number
    product = resolve_erro_product_by_internal_factory_part_number(factory_part_number, db)
    
    # In Demo mode, fallback to any Erro product so user can enter ANY job order
    if not product or not product.customer or product.customer.code != "ERRO":
        if is_demo:
            erro_products = (
                db.query(models.Product)
                .join(models.Customer)
                .filter(models.Customer.code == "ERRO")
                .all()
            )
            if erro_products:
                idx = sum(ord(c) for c in clean_job_order) % len(erro_products)
                product = erro_products[idx]
                factory_part_number = product.internal_factory_part_number or product.item_name or "ERRO-DEMO"
                customer_ref = product.item_name or factory_part_number
                if total_qty <= 0:
                    total_qty = 20 * (product.packed_qty or 1)

    if not product:
        item_hint = f" (Item: {customer_ref})" if customer_ref else ""
        raise HTTPException(
            status_code=404,
            detail=f"Factory P/N '{factory_part_number}'{item_hint} từ công lệnh '{clean_job_order}' chưa được cấu hình cho khách hàng Erro."
        )

    # 3. Ensure product belongs to Customer ERRO
    if not is_demo and (not product.customer or product.customer.code != "ERRO"):
        raise HTTPException(
            status_code=400,
            detail=f"Công lệnh '{clean_job_order}' thuộc khách hàng khác, không thể mở trên trạm cân Erro."
        )

    # 4. Calculate planned cartons
    packed_qty = cast(int, product.packed_qty) or 1
    planned_cartons = math.ceil(total_qty / packed_qty) if total_qty > 0 else 0

    # 5. Count existing cartons already packed for this job order
    packed_cartons_count = db.query(models.Carton).filter(
        models.Carton.job_order == clean_job_order,
        models.Carton.is_reprint == 0,
        models.Carton.status == "SUCCESS"
    ).count()

    # 6. Check for name mismatch
    item_name = (product.item_name or "").strip()
    name_mismatch = (customer_ref.lower() != item_name.lower()) if (customer_ref and item_name) else False

    return schemas.ErroJobOrderResolutionResponse(
        job_order=clean_job_order,
        factory_part_number=factory_part_number,
        customer_ref=customer_ref,
        total_qty=total_qty,
        planned_cartons=planned_cartons,
        packed_cartons_count=packed_cartons_count,
        name_mismatch=name_mismatch,
        lot_number_default=datetime.now().strftime("%Y%m%d") if product.template_type == "erro_01" else None,
        product=product,
    )
