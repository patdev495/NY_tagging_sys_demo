import logging
import math
from datetime import datetime
from typing import cast

from fastapi import HTTPException
from sqlalchemy import func, text
from sqlalchemy.orm import Session

from src.core import models
from src.features.carton.sn_allocator import plan_job_order_slots
from src.features.job_order import schemas

logger = logging.getLogger("JobOrderService")

def get_job_order_from_erp(db: Session, job_order: str):
    """
    Query the Job Order details from the Linked Server 192.168.206.18.
    If database engine is SQLite or if query fails due to database driver / connection issues,
    it falls back to a simulated mock response for local testing/development.
    """
    try:
        is_sqlite = db.get_bind().dialect.name == "sqlite"
    except Exception:
        is_sqlite = False
        
    if is_sqlite:
        logger.info(f"SQLite database detected. Falling back to mock for Job Order '{job_order}'")
        return get_mocked_job_order(db, job_order)

        
    query = text("""
        SELECT wadoco AS [工單], walitm AS [年益料號], wadl01 AS [客戶料號], wauorg/10000 AS [數量] 
        FROM [192.168.206.18].ShopFloorDW.DBO.F4801 
        WHERE wadoco = :job_order
    """)
    try:
        row = db.execute(query, {"job_order": job_order}).fetchone()
        if not row:
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
        if isinstance(e, HTTPException):
            raise e
        logger.error(f"Linked Server query failed: {e}. Raising HTTP error.")
        raise HTTPException(
            status_code=400, 
            detail=f"Không thể kết nối cơ sở dữ liệu ShopFloor hoặc công lệnh không hợp lệ. Chi tiết: {e!s}"
        )

def get_mocked_job_order(db: Session, job_order: str):
    """
    Returns simulated Job Order details based on local products database.
    """
    product = db.query(models.Product).filter(models.Product.item_name == "UACC-Cable-Path-Outdoor-2M-BK").first()
    if not product:
        product = db.query(models.Product).first()
        
    if not product:
        return {
            "job_order": job_order,
            "product_code": "1CAD2420D2BK01NX9",
            "customer_ref": "UACC-Cable-Patch-Outdoor-2M-BK",
            "quantity": 750
        }
        
    ref_name = "UACC-Cable-Patch-Outdoor-2M-BK"
    if product and product.item_name:
        if "Outdoor-2M-BK" not in product.item_name:
            ref_name = product.item_name
    return {
        "job_order": job_order,
        "product_code": "1CAD2420D2BK01NX9",
        "customer_ref": ref_name,
        "quantity": 15 * (product.packed_qty or 1) if product else 750
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
    erp_data = get_job_order_from_erp(db, job_order)
    
    # 2. Find matching product
    cust_ref = str(erp_data.get("customer_ref") or "").strip()
    prod_code = str(erp_data.get("product_code") or "").strip()
    product = find_matching_product(db, cust_ref, prod_code)

    if not product:
        ref_display = cust_ref or prod_code or job_order
        raise HTTPException(
            status_code=400, 
            detail=f"Không tìm thấy con hàng '{ref_display}' tương ứng trong cơ sở dữ liệu."
        )

    if product.customer and product.customer.code.upper() == "ERRO":
        raise HTTPException(
            status_code=400,
            detail="Công lệnh ERRO không cấp slot thùng. Vui lòng dùng trạm cân ERRO.",
        )
        
    # 3. Calculate total cartons
    packed_qty = cast(int, product.packed_qty)
    if packed_qty <= 0:
        raise HTTPException(status_code=400, detail=f"Sản phẩm '{product.item_name}' có packed_qty không hợp lệ ({packed_qty}).")
        
    total_qty = cast(int, erp_data["quantity"])
    total_cartons = math.ceil(total_qty / packed_qty)

    if total_cartons <= 0:
        raise HTTPException(status_code=400, detail=f"Số lượng sản phẩm trong công lệnh ({total_qty}) không đủ để đóng thùng.")
        
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

    # 1. Fetch ERP Job Order details
    erp_data = get_job_order_from_erp(db, clean_job_order)
    factory_part_number = str(erp_data.get("product_code") or "").strip()
    customer_ref = str(erp_data.get("customer_ref") or "").strip()
    total_qty = int(erp_data.get("quantity") or 0)

    # 2. Resolve Erro product by internal factory part number
    from src.features.product.service import resolve_erro_product_by_internal_factory_part_number
    product = resolve_erro_product_by_internal_factory_part_number(factory_part_number, db)
    if not product:
        item_hint = f" (Item: {customer_ref})" if customer_ref else ""
        raise HTTPException(
            status_code=404,
            detail=f"Factory P/N '{factory_part_number}'{item_hint} từ công lệnh '{clean_job_order}' chưa được cấu hình cho khách hàng Erro."
        )

    # 3. Ensure product belongs to Customer ERRO
    if not product.customer or product.customer.code != "ERRO":
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
