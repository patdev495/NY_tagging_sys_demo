import datetime
import re
from dataclasses import dataclass

from sqlalchemy import func
from sqlalchemy.orm import Session

from src.core import models

SEQUENCE_WIDTH = 5


@dataclass(frozen=True)
class CartonSNPlan:
    prefix: str
    sequence: int
    carton_sn: str


def current_yymm() -> str:
    return datetime.datetime.now().strftime("%y%m")


def build_prefix(product: models.Product, yymm: str | None = None) -> str:
    return f"{product.start_part or ''}{yymm or current_yymm()}{product.middle_part or ''}"


def format_carton_sn(prefix: str, sequence: int) -> str:
    return f"{prefix}{str(sequence).zfill(SEQUENCE_WIDTH)}"


def parse_sequence(carton_sn: str | None, prefix: str | None = None) -> int:
    if not carton_sn:
        return 0
    if prefix and carton_sn.startswith(prefix):
        sequence_text = carton_sn[len(prefix):]
    else:
        sequence_text = carton_sn[-SEQUENCE_WIDTH:]
    if not re.fullmatch(r"\d+", sequence_text):
        return 0
    try:
        return int(sequence_text)
    except ValueError:
        return 0


def _max_carton_sn(db: Session, prefix: str, product_id: int | None = None, lock: bool = False) -> str | None:
    query = db.query(func.max(models.Carton.carton_sn)).filter(
        models.Carton.carton_sn.like(f"{prefix}%"),
        models.Carton.is_reprint == 0,
    )
    if product_id is not None:
        query = query.filter(models.Carton.product_id == product_id)
    if lock:
        query = query.with_for_update()
    return query.scalar()


def _max_slot_sn(db: Session, prefix: str, product_id: int | None = None, lock: bool = False) -> str | None:
    query = db.query(func.max(models.JobOrderCartonSlot.carton_sn)).filter(
        models.JobOrderCartonSlot.carton_sn.like(f"{prefix}%")
    )
    if product_id is not None:
        query = query.filter(models.JobOrderCartonSlot.product_id == product_id)
    if lock:
        query = query.with_for_update()
    return query.scalar()


def next_sequence(
    db: Session,
    prefix: str,
    product_id: int | None = None,
    include_slots: bool = True,
    lock: bool = False,
) -> int:
    candidates = [_max_carton_sn(db, prefix, product_id=product_id, lock=lock)]
    if include_slots:
        candidates.append(_max_slot_sn(db, prefix, product_id=product_id, lock=lock))
    return max(parse_sequence(sn, prefix) for sn in candidates) + 1


def plan_next_carton_sn(
    db: Session,
    product: models.Product,
    custom_sn: int | None = None,
    custom_yymm: str | None = None,
    include_slots: bool = True,
    lock: bool = False,
) -> CartonSNPlan:
    prefix = build_prefix(product, custom_yymm)
    sequence = custom_sn if custom_sn is not None else next_sequence(
        db,
        prefix,
        include_slots=include_slots,
        lock=lock,
    )
    return CartonSNPlan(
        prefix=prefix,
        sequence=sequence,
        carton_sn=format_carton_sn(prefix, sequence),
    )


def plan_job_order_slots(
    db: Session,
    product: models.Product,
    total_cartons: int,
    yymm: str | None = None,
    lock: bool = False,
) -> list[CartonSNPlan]:
    prefix = build_prefix(product, yymm)
    start_sequence = next_sequence(
        db,
        prefix,
        include_slots=True,
        lock=lock,
    )
    return [
        CartonSNPlan(
            prefix=prefix,
            sequence=start_sequence + offset,
            carton_sn=format_carton_sn(prefix, start_sequence + offset),
        )
        for offset in range(total_cartons)
    ]
