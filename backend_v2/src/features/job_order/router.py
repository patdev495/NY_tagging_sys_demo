
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from src.core.database import get_db

from . import schemas, service

router = APIRouter(prefix="/job-orders", tags=["Job Order"])

@router.get("/resolve-erro-job-order", response_model=schemas.ErroJobOrderResolutionResponse)
def resolve_erro_job_order(job_order: str, db: Session = Depends(get_db)):
    """
    Resolve an Erro Product and packing parameters from a ShopFloorDW Job Order (wadoco).
    """
    return service.resolve_erro_job_order(db, job_order)

@router.get("/{job_order}", response_model=schemas.JobOrderDetailsResponse)
def get_job_order_details(job_order: str, db: Session = Depends(get_db)):
    """
    Get job order details from Linked Server, find matching product,
    and automatically allocate carton slots if not yet allocated.
    """
    return service.get_or_create_job_order_slots(db, job_order)

@router.get("/{job_order}/slots", response_model=list[schemas.JobOrderSlotResponse])
def get_job_order_slots(job_order: str, db: Session = Depends(get_db)):
    """
    Get list of pre-allocated carton slots and their statuses for a job order.
    """
    return service.get_job_order_slots_list(db, job_order)
