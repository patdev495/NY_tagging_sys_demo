import datetime
from collections.abc import Iterable
from typing import cast as typing_cast

from fastapi import HTTPException
from sqlalchemy import or_
from sqlalchemy.orm import Session

from src.core import models
from src.features.carton import print_attempts


def get_pending_slot_for_carton_creation(
    db: Session,
    *,
    slot_id: int | None,
    job_order: str | None,
    product_id: int,
) -> models.JobOrderCartonSlot:
    if not job_order:
        raise HTTPException(status_code=400, detail="Job Order is required for carton creation")
    if slot_id is None:
        raise HTTPException(status_code=400, detail="A carton slot is required for a Job Order")

    slot = db.query(models.JobOrderCartonSlot).filter(
        models.JobOrderCartonSlot.id == slot_id,
        models.JobOrderCartonSlot.job_order == job_order,
        models.JobOrderCartonSlot.product_id == product_id,
    ).with_for_update().first()
    if not slot:
        raise HTTPException(status_code=400, detail="Carton slot does not belong to this Job Order and Product")
    if slot.status != "PENDING" or slot.carton_id is not None:
        raise HTTPException(status_code=409, detail="Carton slot has already been completed")
    return slot


def slots_for_carton_attempt_group(
    db: Session,
    carton: models.Carton,
    carton_attempt_ids: Iterable[int],
) -> list[models.JobOrderCartonSlot]:
    attempt_ids = list(carton_attempt_ids)
    return db.query(models.JobOrderCartonSlot).filter(
        or_(
            models.JobOrderCartonSlot.carton_id.in_(attempt_ids),
            (
                (models.JobOrderCartonSlot.job_order == carton.job_order)
                & (models.JobOrderCartonSlot.carton_sn == carton.carton_sn)
            ),
        )
    ).all()


def ensure_slots_not_shipped(slots: Iterable[models.JobOrderCartonSlot]) -> None:
    if any(slot.shipped == 1 for slot in slots):
        raise HTTPException(
            status_code=409,
            detail="Cannot delete a carton that has already been shipped",
        )


def release_slots(slots: Iterable[models.JobOrderCartonSlot]) -> None:
    for slot in slots:
        slot.status = "PENDING"  # type: ignore
        slot.scanned_at = None  # type: ignore
        slot.carton_id = None  # type: ignore


def release_original_slot_for_carton(db: Session, carton: models.Carton) -> None:
    slot = db.query(models.JobOrderCartonSlot).filter(
        models.JobOrderCartonSlot.carton_id == carton.id
    ).first()
    if slot:
        release_slots([slot])


def complete_slot_for_success(db: Session, carton: models.Carton) -> None:
    if not carton.job_order:
        return

    slot = db.query(models.JobOrderCartonSlot).filter(
        models.JobOrderCartonSlot.job_order == carton.job_order,
        models.JobOrderCartonSlot.carton_sn == carton.carton_sn,
    ).first()
    if not slot:
        return

    original_carton_id = print_attempts.get_original_carton_id(db, carton)
    if original_carton_id is None:
        return

    slot.status = "SCANNED"  # type: ignore
    slot.carton_id = original_carton_id  # type: ignore
    slot.scanned_at = datetime.datetime.now()  # type: ignore


def release_slot_for_failed_original(db: Session, carton: models.Carton) -> None:
    if typing_cast(int, carton.is_reprint) == 1:
        return
    release_original_slot_for_carton(db, carton)
