import datetime
from typing import cast as typing_cast

from fastapi import HTTPException
from sqlalchemy import Date, case, cast, func
from sqlalchemy.orm import Session, joinedload, defer

from src.core import models
from src.features.carton import print_attempts, slot_lifecycle
from src.features.carton.item_sn_conflicts import find_ui_item_sn_conflicts


def build_carton_query(
    db: Session,
    search: str | None = None,
    product_id: int | None = None,
    status: str | None = None,
    start_date: str | None = None,
    end_date: str | None = None,
    customer_id: int | None = None,
    job_order: str | None = None,
    po_number: str | None = None,
):
    # Subquery to count the total print attempts for each unique carton_sn
    count_sub = db.query(
        models.Carton.carton_sn.label("carton_sn"),
        func.count(models.Carton.id).label("print_count")
    ).group_by(models.Carton.carton_sn).subquery()

    # Keep every print attempt so Admin History preserves the original Carton
    # alongside all Reprints for the same Carton SN.
    base_query = db.query(models.Carton, count_sub.c.print_count).outerjoin(
        count_sub, models.Carton.carton_sn == count_sub.c.carton_sn
    ).options(joinedload(models.Carton.product).joinedload(models.Product.customer))

    if customer_id:
        base_query = base_query.join(models.Product, models.Carton.product_id == models.Product.id).filter(
            models.Product.customer_id == customer_id
        )

    if search:
        base_query = base_query.filter(models.Carton.carton_sn.like(f"%{search}%"))
    if product_id:
        base_query = base_query.filter(models.Carton.product_id == product_id)
    if status:
        base_query = base_query.filter(models.Carton.status == status)

    if start_date:
        try:
            start_dt = datetime.datetime.strptime(start_date, "%Y-%m-%d")
            base_query = base_query.filter(models.Carton.created_at >= start_dt)
        except ValueError:
            pass

    if end_date:
        try:
            end_dt = datetime.datetime.strptime(end_date, "%Y-%m-%d").replace(hour=23, minute=59, second=59, microsecond=999999)
            base_query = base_query.filter(models.Carton.created_at <= end_dt)
        except ValueError:
            pass

    if job_order:
        base_query = base_query.filter(models.Carton.job_order.like(f"%{job_order}%"))
    if po_number:
        base_query = base_query.filter(models.Carton.po_number.like(f"%{po_number}%"))

    return base_query

def get_cartons(
    db: Session, 
    skip: int = 0, 
    limit: int = 50, 
    search: str | None = None,
    product_id: int | None = None,
    status: str | None = None,
    start_date: str | None = None,
    end_date: str | None = None,
    customer_id: int | None = None,
    job_order: str | None = None,
    po_number: str | None = None,
):
    base_query = build_carton_query(
        db=db,
        search=search,
        product_id=product_id,
        status=status,
        start_date=start_date,
        end_date=end_date,
        customer_id=customer_id,
        job_order=job_order,
        po_number=po_number,
    )
        
    total = base_query.count()
    results = (
        base_query.options(defer(models.Carton.btxml))
        .order_by(models.Carton.id.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )

    # Batch calculate items_count in 1 query instead of N+1 queries
    reprint_cartons = [c for c, _ in results if c.is_reprint == 1]
    orig_carton_map: dict[str, int] = {}
    if reprint_cartons:
        reprint_sns = [c.carton_sn for c in reprint_cartons if c.carton_sn]
        if reprint_sns:
            orig_rows = (
                db.query(models.Carton.carton_sn, models.Carton.id)
                .filter(models.Carton.carton_sn.in_(reprint_sns), models.Carton.is_reprint == 0)
                .all()
            )
            for sn, orig_id in orig_rows:
                if sn and orig_id and sn not in orig_carton_map:
                    orig_carton_map[sn] = orig_id

    carton_target_ids: dict[int, int] = {}
    for carton, _ in results:
        target_id = orig_carton_map.get(carton.carton_sn) if carton.is_reprint == 1 else None
        carton_target_ids[carton.id] = target_id or carton.id

    all_target_ids = list(set(carton_target_ids.values()))
    counts_map: dict[int, int] = {}
    if all_target_ids:
        counts = (
            db.query(models.CartonItem.carton_id, func.count(models.CartonItem.id))
            .filter(models.CartonItem.carton_id.in_(all_target_ids))
            .group_by(models.CartonItem.carton_id)
            .all()
        )
        counts_map = {cid: cnt for cid, cnt in counts if cid is not None}

    items = []
    for carton, print_count in results:
        carton.reprint_count = max((print_count or 1) - 1, 0)
        target_id = carton_target_ids.get(carton.id, carton.id)
        carton.items_count = counts_map.get(target_id, 0)
        items.append(carton)

    return {"total": total, "items": items}

def export_cartons_to_excel(
    db: Session,
    mode: str = "summary",
    search: str | None = None,
    product_id: int | None = None,
    status: str | None = None,
    start_date: str | None = None,
    end_date: str | None = None,
    customer_id: int | None = None,
    job_order: str | None = None,
    po_number: str | None = None,
) -> bytes:
    from .excel_export import generate_carton_excel

    base_query = build_carton_query(
        db=db,
        search=search,
        product_id=product_id,
        status=status,
        start_date=start_date,
        end_date=end_date,
        customer_id=customer_id,
        job_order=job_order,
        po_number=po_number,
    ).filter(
        models.Carton.is_reprint == 0
    ).options(defer(models.Carton.btxml))

    if mode == "detailed":
        base_query = base_query.options(joinedload(models.Carton.items))

    results = base_query.order_by(models.Carton.id.desc()).all()
    cartons = [carton for carton, _ in results]
    
    return generate_carton_excel(cartons, mode=mode)

def get_carton_detail(db: Session, carton_id: int):
    carton = db.query(models.Carton).options(
        joinedload(models.Carton.product),
        joinedload(models.Carton.items)
    ).filter(models.Carton.id == carton_id).first()
    
    if not carton:
        raise HTTPException(status_code=404, detail="Carton not found")
        
    original_carton = print_attempts.get_original_carton(db, carton)
    items = original_carton.items if original_carton else []
    if typing_cast(int, carton.is_reprint) == 1:
        carton.items = items

    carton.items_count = len(typing_cast(list, items))
    
    print_history = print_attempts.print_history_for_carton(db, carton)
    orig_item_count = print_attempts.item_count_for_group(db, carton)
    
    for h in print_history:
        h.items_count = orig_item_count
        h.reprint_count = 0  # Not applicable for history items
        
    carton.print_history = print_history
    carton.reprint_count = len(print_history)
    
    return carton

def search_carton_by_sn(carton_sn: str, db: Session):
    carton = db.query(models.Carton).filter(
        models.Carton.carton_sn == carton_sn,
        models.Carton.is_reprint == 0,
    ).order_by(models.Carton.id.desc()).first()
    if not carton:
        raise HTTPException(status_code=404, detail="Carton not found")
    
    return get_carton_detail(db, carton.id)

def search_by_item_sn(item_sn: str, db: Session):
    # Find the item first
    item = db.query(models.CartonItem).filter(models.CartonItem.item_sn == item_sn).order_by(models.CartonItem.id.desc()).first()
    if not item:
        raise HTTPException(status_code=404, detail="Item S/N not found in any carton")
    
    # Return the associated carton with details
    return get_carton_detail(db, typing_cast(int, item.carton_id))


def get_ui_item_sn_conflicts(item_sn: str, db: Session, exclude_carton_id: int | None = None):
    """Return a small, index-friendly summary of UI Cartons owning an Item SN."""
    return {
        "item_sn": item_sn,
        "conflicts": find_ui_item_sn_conflicts(db, [item_sn], exclude_carton_id).get(item_sn, []),
    }

def delete_carton(db: Session, carton_id: int):
    carton = db.query(models.Carton).filter(models.Carton.id == carton_id).first()
    if not carton:
        raise HTTPException(status_code=404, detail="Carton not found")

    carton_attempts = print_attempts.get_carton_attempts(db, carton)
    carton_attempt_ids = [attempt.id for attempt in carton_attempts]
    
    slots = slot_lifecycle.slots_for_carton_attempt_group(db, carton, carton_attempt_ids)
    slot_lifecycle.ensure_slots_not_shipped(slots)
    slot_lifecycle.release_slots(slots)

    if carton_attempt_ids:
        db.query(models.UIItemSNClaim).filter(models.UIItemSNClaim.carton_id.in_(carton_attempt_ids)).delete(
            synchronize_session=False
        )
        db.query(models.CartonItem).filter(models.CartonItem.carton_id.in_(carton_attempt_ids)).delete(synchronize_session=False)
    
    for attempt in carton_attempts:
        db.delete(attempt)

    db.commit()
    return {"message": "Carton deleted successfully", "deleted_count": len(carton_attempts)}

def get_packaging_statistics(db: Session, start_date: str, end_date: str):
    # Parse dates
    start_dt = datetime.datetime.strptime(start_date, "%Y-%m-%d")
    end_dt = datetime.datetime.strptime(end_date + " 23:59:59.999", "%Y-%m-%d %H:%M:%S.%f")
    
    # 1. Summary Metrics
    total_cartons = db.query(models.Carton).filter(
        models.Carton.created_at >= start_dt,
        models.Carton.created_at <= end_dt
    ).count()
    
    success_cartons = db.query(models.Carton).filter(
        models.Carton.created_at >= start_dt,
        models.Carton.created_at <= end_dt,
        models.Carton.status == "SUCCESS"
    ).count()
    
    failed_cartons = db.query(models.Carton).filter(
        models.Carton.created_at >= start_dt,
        models.Carton.created_at <= end_dt,
        models.Carton.status == "FAILED"
    ).count()
    
    reprint_cartons = db.query(models.Carton).filter(
        models.Carton.created_at >= start_dt,
        models.Carton.created_at <= end_dt,
        models.Carton.is_reprint == 1
    ).count()
    
    total_items = db.query(models.CartonItem).join(
        models.Carton, models.CartonItem.carton_id == models.Carton.id
    ).filter(
        models.Carton.created_at >= start_dt,
        models.Carton.created_at <= end_dt
    ).count()
    
    # 2. Daily Breakdown
    # MSSQL/SQLite compatible grouping
    daily_results = db.query(
        cast(models.Carton.created_at, Date).label("date"),
        func.count(models.Carton.id).label("total"),
        func.sum(case((models.Carton.status == "SUCCESS", 1), else_=0)).label("success"),
        func.sum(case((models.Carton.is_reprint == 1, 1), else_=0)).label("reprint")
    ).filter(
        models.Carton.created_at >= start_dt,
        models.Carton.created_at <= end_dt
    ).group_by(
        cast(models.Carton.created_at, Date)
    ).order_by(
        cast(models.Carton.created_at, Date)
    ).all()
    
    daily_breakdown = []
    for r in daily_results:
        daily_breakdown.append({
            "date": str(r.date),
            "total": int(r.total or 0),
            "success": int(r.success or 0),
            "reprint": int(r.reprint or 0)
        })
        
    # 3. Product Breakdown
    product_results = db.query(
        models.Product.item_name.label("item_name"),
        func.count(models.Carton.id).label("total"),
        func.sum(case((models.Carton.is_reprint == 1, 1), else_=0)).label("reprint")
    ).join(
        models.Carton, models.Carton.product_id == models.Product.id
    ).filter(
        models.Carton.created_at >= start_dt,
        models.Carton.created_at <= end_dt
    ).group_by(
        models.Product.item_name
    ).order_by(
        func.count(models.Carton.id).desc()
    ).all()
    
    product_breakdown = []
    for r in product_results:
        product_breakdown.append({
            "item_name": str(r.item_name),
            "total": int(r.total or 0),
            "reprint": int(r.reprint or 0)
        })
        
    return {
        "total_cartons": total_cartons,
        "success_cartons": success_cartons,
        "failed_cartons": failed_cartons,
        "reprint_cartons": reprint_cartons,
        "total_items": total_items,
        "daily_breakdown": daily_breakdown,
        "product_breakdown": product_breakdown
    }


def get_job_order_statistics(db: Session, job_order: str):
    # 1. Total attempts and reprint attempts under this job_order
    total_attempts = db.query(models.Carton).filter(
        models.Carton.job_order == job_order
    ).count()

    reprint_attempts = db.query(models.Carton).filter(
        models.Carton.job_order == job_order,
        models.Carton.is_reprint == 1
    ).count()

    # 2. Get the latest print attempt per carton_sn in this job_order
    max_id_sub = db.query(
        func.max(models.Carton.id).label("max_id")
    ).filter(
        models.Carton.job_order == job_order
    ).group_by(models.Carton.carton_sn).subquery()

    count_sub = db.query(
        models.Carton.carton_sn.label("carton_sn"),
        func.count(models.Carton.id).label("print_count")
    ).filter(
        models.Carton.job_order == job_order
    ).group_by(models.Carton.carton_sn).subquery()

    results = db.query(models.Carton, count_sub.c.print_count).join(
        max_id_sub, models.Carton.id == max_id_sub.c.max_id
    ).outerjoin(
        count_sub, models.Carton.carton_sn == count_sub.c.carton_sn
    ).options(joinedload(models.Carton.product)).all()

    items = []
    success_count = 0
    failed_count = 0
    total_items = 0
    product_stats = {}

    for carton, print_count in results:
        # Populate carton properties
        item_count = print_attempts.item_count_for_group(db, carton)
        carton.items_count = item_count
        carton.reprint_count = max((print_count or 1) - 1, 0)
        items.append(carton)

        # Count total items
        total_items += item_count

        # Count success vs failed
        if carton.status == "SUCCESS":
            success_count += 1
        else:
            failed_count += 1

        # Product breakdown
        prod = carton.product
        if prod:
            prod_id = typing_cast(int, prod.id)
            if prod_id not in product_stats:
                product_stats[prod_id] = {
                    "product_id": prod_id,
                    "item_name": str(prod.item_name),
                    "total_cartons": 0,
                    "success_cartons": 0,
                    "failed_cartons": 0
                }
            product_stats[prod_id]["total_cartons"] += 1
            if carton.status == "SUCCESS":
                product_stats[prod_id]["success_cartons"] += 1
            else:
                product_stats[prod_id]["failed_cartons"] += 1

    return {
        "job_order": job_order,
        "total_cartons": len(items),
        "success_cartons": success_count,
        "failed_cartons": failed_count,
        "total_attempts": total_attempts,
        "reprint_attempts": reprint_attempts,
        "total_items": total_items,
        "product_breakdown": list(product_stats.values()),
        "cartons": items
    }
