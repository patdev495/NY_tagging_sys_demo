import logging

from fastapi import HTTPException
from sqlalchemy import case, desc, func, or_
from sqlalchemy.orm import Session

from src.core import models

from .schemas import (
    JobOrderSlotCancellationCheck,
    JobOrderSlotCancellationResult,
    JobOrderSlotDetail,
    JobOrderSummary,
    POLotRunSummary,
)

logger = logging.getLogger("ProductionRunService")

def get_job_orders_summary(db: Session) -> list[JobOrderSummary]:
    results = db.query(
        models.JobOrderCartonSlot.job_order,
        models.JobOrderCartonSlot.product_id,
        models.Product.item_name,
        models.Customer.code,
        func.count(models.JobOrderCartonSlot.id).label("total_slots"),
        func.sum(case((models.JobOrderCartonSlot.status == "SCANNED", 1), else_=0)).label("scanned_slots"),
        func.sum(case((models.JobOrderCartonSlot.status == "PENDING", 1), else_=0)).label("pending_slots"),
        func.sum(case((models.JobOrderCartonSlot.shipped == 1, 1), else_=0)).label("shipped_slots"),
        func.max(models.JobOrderCartonSlot.scanned_at).label("latest_scan_at")
    ).join(
        models.Product, models.JobOrderCartonSlot.product_id == models.Product.id
    ).outerjoin(
        models.Customer, models.Product.customer_id == models.Customer.id
    ).filter(
        or_(
            models.Customer.code.is_(None),
            func.upper(models.Customer.code) != "ERRO",
        )
    ).group_by(
        models.JobOrderCartonSlot.job_order,
        models.JobOrderCartonSlot.product_id,
        models.Product.item_name,
        models.Customer.code
    ).order_by(
        desc("latest_scan_at"),
        models.JobOrderCartonSlot.job_order.desc()
    ).all()

    summaries = []
    for r in results:
        total = r.total_slots or 0
        scanned = r.scanned_slots or 0
        pending = r.pending_slots or 0
        shipped = r.shipped_slots or 0
        comp_rate = round((scanned / total * 100), 1) if total > 0 else 0.0

        summaries.append(
            JobOrderSummary(
                job_order=r.job_order,
                product_id=r.product_id,
                product_name=r.item_name or "N/A",
                customer_code=r.code or "N/A",
                total_slots=total,
                scanned_slots=scanned,
                pending_slots=pending,
                shipped_slots=shipped,
                completion_rate=comp_rate,
                latest_scan_at=r.latest_scan_at
            )
        )
    return summaries

def get_job_order_slots(db: Session, job_order: str) -> list[JobOrderSlotDetail]:
    slots = db.query(models.JobOrderCartonSlot).join(
        models.Product, models.JobOrderCartonSlot.product_id == models.Product.id
    ).outerjoin(
        models.Customer, models.Product.customer_id == models.Customer.id
    ).filter(
        models.JobOrderCartonSlot.job_order == job_order,
        or_(
            models.Customer.code.is_(None),
            func.upper(models.Customer.code) != "ERRO",
        ),
    ).order_by(models.JobOrderCartonSlot.carton_number.asc()).all()

    return [JobOrderSlotDetail.model_validate(s) for s in slots]


def check_job_order_slot_cancellation(
    db: Session, job_order: str
) -> JobOrderSlotCancellationCheck:
    slots = db.query(models.JobOrderCartonSlot).filter(
        models.JobOrderCartonSlot.job_order == job_order
    ).all()
    slot_completion_count = sum(
        slot.status != "PENDING" or slot.carton_id is not None or slot.shipped == 1
        for slot in slots
    )
    carton_count = db.query(func.count(models.Carton.id)).filter(
        models.Carton.job_order == job_order
    ).scalar() or 0
    scanned_slots = max(slot_completion_count, carton_count)
    return JobOrderSlotCancellationCheck(
        job_order=job_order,
        total_slots=len(slots),
        scanned_slots=scanned_slots,
        can_cancel=bool(slots) and scanned_slots == 0,
    )


def cancel_job_order_slot_allocation(
    db: Session, job_order: str
) -> JobOrderSlotCancellationResult:
    slots = db.query(models.JobOrderCartonSlot).filter(
        models.JobOrderCartonSlot.job_order == job_order
    ).with_for_update().all()
    if not slots:
        raise HTTPException(status_code=404, detail="Công lệnh chưa được cấp slot.")

    has_completed_carton = any(
        slot.status != "PENDING" or slot.carton_id is not None or slot.shipped == 1
        for slot in slots
    )
    has_carton_record = db.query(models.Carton.id).filter(
        models.Carton.job_order == job_order
    ).first() is not None
    if has_completed_carton or has_carton_record:
        raise HTTPException(
            status_code=409,
            detail="Không thể xoá cấp phát vì công lệnh đã có thùng được quét hoặc xuất kho.",
        )

    deleted_slots = len(slots)
    try:
        for slot in slots:
            db.delete(slot)
        db.commit()
    except Exception:
        db.rollback()
        raise

    return JobOrderSlotCancellationResult(
        job_order=job_order,
        deleted_slots=deleted_slots,
    )


def get_po_lot_runs(db: Session) -> list[POLotRunSummary]:
    results = db.query(
        models.Carton.po_number,
        models.Carton.lot_number,
        models.Product.item_name,
        models.Customer.code,
        models.Carton.date_code,
        func.count(models.Carton.id).label("total_cartons"),
        func.sum(func.coalesce(models.Carton.weight, 0.0)).label("total_weight"),
        func.max(models.Carton.created_at).label("latest_packed_at")
    ).join(
        models.Product, models.Carton.product_id == models.Product.id
    ).outerjoin(
        models.Customer, models.Product.customer_id == models.Customer.id
    ).filter(
        models.Carton.po_number.isnot(None),
        models.Carton.po_number != ""
    ).group_by(
        models.Carton.po_number,
        models.Carton.lot_number,
        models.Product.item_name,
        models.Customer.code,
        models.Carton.date_code
    ).order_by(
        desc("latest_packed_at")
    ).all()

    runs = []
    for r in results:
        runs.append(
            POLotRunSummary(
                po_number=r.po_number or "N/A",
                lot_number=r.lot_number or "N/A",
                product_name=r.item_name or "N/A",
                customer_code=r.code or "N/A",
                date_code=r.date_code,
                total_cartons=r.total_cartons or 0,
                total_weight=round(float(r.total_weight or 0.0), 2),
                latest_packed_at=r.latest_packed_at
            )
        )
    return runs
