"""Carton ID allocation for the PD016906 Erro 05 (Pegatron NN9) label."""

from dataclasses import dataclass
from datetime import datetime

from fastapi import HTTPException
from sqlalchemy.orm import Session

from src.core import models

ERRO_05_SEQUENCE_WIDTH = 5
ERRO_05_MIN_SEQUENCE = 50001
ERRO_05_MAX_SEQUENCE = 99999
ERRO_05_DEFAULT_PREFIX = "MC220TW1"


@dataclass(frozen=True)
class Erro05CartonSNPlan:
    carton_sn: str
    sequence: int
    date_code: str
    pkg_prefix: str


def parse_erro_05_sequence(carton_sn: str | None) -> int | None:
    if not carton_sn or len(carton_sn) < ERRO_05_SEQUENCE_WIDTH:
        return None

    seq_str = carton_sn[-ERRO_05_SEQUENCE_WIDTH:]
    if not seq_str.isdigit():
        return None

    val = int(seq_str)
    return val if ERRO_05_MIN_SEQUENCE <= val <= ERRO_05_MAX_SEQUENCE else None


def get_month_boundaries(dt: datetime) -> tuple[datetime, datetime]:
    start_of_month = datetime(dt.year, dt.month, 1, 0, 0, 0)
    if dt.month == 12:
        start_of_next_month = datetime(dt.year + 1, 1, 1, 0, 0, 0)
    else:
        start_of_next_month = datetime(dt.year, dt.month + 1, 1, 0, 0, 0)
    return start_of_month, start_of_next_month


def next_erro_05_sequence(db: Session, target_time: datetime, lock: bool = False) -> int:
    start_of_month, start_of_next_month = get_month_boundaries(target_time)

    if lock:
        # Lock all erro_05 products so concurrent workers serialize allocations
        (
            db.query(models.Product.id)
            .filter(models.Product.template_type == "erro_05")
            .with_for_update()
            .all()
        )

    query = (
        db.query(models.Carton.carton_sn)
        .join(models.Product, models.Carton.product_id == models.Product.id)
        .filter(
            models.Product.template_type == "erro_05",
            models.Carton.is_reprint == 0,
            models.Carton.created_at >= start_of_month,
            models.Carton.created_at < start_of_next_month,
        )
    )
    sequences = [parse_erro_05_sequence(row[0]) for row in query.all()]
    valid_sequences = [s for s in sequences if s is not None]

    if not valid_sequences:
        return ERRO_05_MIN_SEQUENCE

    max_seq = max(valid_sequences)
    next_seq = max_seq + 1

    if next_seq > ERRO_05_MAX_SEQUENCE:
        raise HTTPException(
            status_code=400,
            detail=f"Erro 05 Carton Sequence range ({ERRO_05_MIN_SEQUENCE}-{ERRO_05_MAX_SEQUENCE}) exceeded for {target_time.strftime('%Y-%m')}."
        )

    return next_seq


def plan_next_erro_05_carton_sn(
    db: Session,
    product: models.Product,
    *,
    printed_at: datetime | None = None,
    lock: bool = False,
) -> Erro05CartonSNPlan:
    now = printed_at or datetime.now()
    pkg_prefix = (getattr(product, "pkg_prefix", None) or ERRO_05_DEFAULT_PREFIX).strip()
    if not pkg_prefix:
        pkg_prefix = ERRO_05_DEFAULT_PREFIX

    yy = now.strftime("%y")
    ww = f"{now.isocalendar()[1]:02d}"
    date_code = f"{yy}{ww}"

    sequence = next_erro_05_sequence(db, target_time=now, lock=lock)
    carton_sn = f"{pkg_prefix}2{date_code}{sequence:05d}"

    return Erro05CartonSNPlan(
        carton_sn=carton_sn,
        sequence=sequence,
        date_code=date_code,
        pkg_prefix=pkg_prefix,
    )
