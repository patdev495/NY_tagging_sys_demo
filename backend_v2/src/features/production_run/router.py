
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from src.core.database import get_db
from src.core.models import User
from src.features.auth.dependencies import get_current_user, require_admin

from . import service
from .schemas import (
    JobOrderSlotCancellationCheck,
    JobOrderSlotCancellationResult,
    JobOrderSlotDetail,
    JobOrderSummary,
    POLotRunSummary,
)

router = APIRouter(prefix="/admin/production-runs", tags=["Production Runs"])

@router.get("/job-orders", response_model=list[JobOrderSummary])
def list_job_orders_summary(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Liệt kê danh sách các công lệnh Job Order cùng tiến độ đóng gói (slots).
    Hỗ trợ cả quyền Admin và QA.
    """
    return service.get_job_orders_summary(db)

@router.get("/job-orders/{job_order}/slots", response_model=list[JobOrderSlotDetail])
def list_job_order_slots(
    job_order: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Lấy danh sách chi tiết các vị trí slot thùng (1..N) của một Job Order.
    Hỗ trợ cả quyền Admin và QA.
    """
    return service.get_job_order_slots(db, job_order)


@router.get(
    "/job-orders/{job_order}/cancellation-check",
    response_model=JobOrderSlotCancellationCheck,
)
def check_job_order_slot_cancellation(
    job_order: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """Kiểm tra liệu một công lệnh UI có thể xoá cấp phát slot hay không."""
    return service.check_job_order_slot_cancellation(db, job_order.strip())


@router.delete(
    "/job-orders/{job_order}/slots",
    response_model=JobOrderSlotCancellationResult,
)
def cancel_job_order_slot_allocation(
    job_order: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """Xoá toàn bộ slot chưa quét của một công lệnh UI."""
    return service.cancel_job_order_slot_allocation(db, job_order.strip())


@router.get("/po-runs", response_model=list[POLotRunSummary])
def list_po_lot_runs(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Liệt kê danh sách các đợt cân đóng hàng theo cặp PO Number & Lot Number.
    Hỗ trợ cả quyền Admin và QA.
    """
    return service.get_po_lot_runs(db)
