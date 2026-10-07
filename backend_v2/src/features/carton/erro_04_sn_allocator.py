"""Carton ID allocation for the PD027032 Erro 04 label."""

from dataclasses import dataclass
from datetime import datetime

from fastapi import HTTPException
from sqlalchemy import or_
from sqlalchemy.orm import Session

from src.core import models

ERRO_04_ALPHABET = "0123456789ABCDEFGHJKMNPQRSTVWXYZ"
ERRO_04_SEQUENCE_WIDTH = 4
ERRO_04_YEAR_CODES = {
    2023: "3", 2024: "4", 2025: "5", 2026: "6", 2027: "7", 2028: "8",
    2029: "9", 2030: "A", 2031: "B", 2032: "C", 2033: "D", 2034: "E",
}


@dataclass(frozen=True)
class Erro04CartonSNPlan:
    carton_sn: str
    sequence: int
    date_code: str
    carton_id_prefix: str


def format_erro_04_sequence(sequence: int) -> str:
    if sequence < 1 or sequence >= len(ERRO_04_ALPHABET) ** ERRO_04_SEQUENCE_WIDTH:
        raise HTTPException(status_code=400, detail="Erro 04 Carton Sequence has reached its supported range.")

    value = sequence
    chars = []
    for _ in range(ERRO_04_SEQUENCE_WIDTH):
        value, remainder = divmod(value, len(ERRO_04_ALPHABET))
        chars.append(ERRO_04_ALPHABET[remainder])
    return "".join(reversed(chars))


def parse_erro_04_sequence(carton_sn: str | None) -> int | None:
    if not carton_sn or len(carton_sn) < ERRO_04_SEQUENCE_WIDTH:
        return None

    sequence_text = carton_sn[-ERRO_04_SEQUENCE_WIDTH:]
    if any(char not in ERRO_04_ALPHABET for char in sequence_text):
        return None

    value = 0
    for char in sequence_text:
        value = value * len(ERRO_04_ALPHABET) + ERRO_04_ALPHABET.index(char)
    return value if value >= 1 else None


def pd027032_date_code(printed_at: datetime) -> str:
    try:
        year = ERRO_04_YEAR_CODES[printed_at.year]
    except KeyError as error:
        raise HTTPException(status_code=400, detail=f"PD027032 does not define a year code for {printed_at.year}.") from error
    return f"{year}{ERRO_04_ALPHABET[printed_at.month]}{ERRO_04_ALPHABET[printed_at.day]}"


def next_erro_04_sequence(db: Session, year: int | None = None, lock: bool = False) -> int:
    current_year = year or datetime.now().year
    year_code = ERRO_04_YEAR_CODES.get(current_year)
    if not year_code:
        raise HTTPException(status_code=400, detail=f"PD027032 does not define a year code for {current_year}.")

    if lock:
        # H and K intentionally share one sequence. Lock every Erro 04 Product
        # before reading the latest Carton so allocations from separate products
        # serialize on the same database rows.
        (
            db.query(models.Product.id)
            .filter(models.Product.template_type == "erro_04")
            .with_for_update()
            .all()
        )

    filters = [
        models.Product.template_type == "erro_04",
        models.Carton.is_reprint == 0,
        or_(
            models.Carton.carton_sn.like(f"H{year_code}%"),
            models.Carton.carton_sn.like(f"K{year_code}%"),
        ),
    ]

    query = (
        db.query(models.Carton.carton_sn)
        .join(models.Product, models.Carton.product_id == models.Product.id)
        .filter(*filters)
    )
    sequences = [parse_erro_04_sequence(row[0]) for row in query.all()]
    return max((sequence for sequence in sequences if sequence is not None), default=0) + 1


def plan_next_erro_04_carton_sn(
    db: Session,
    product: models.Product,
    *,
    printed_at: datetime | None = None,
    lock: bool = False,
) -> Erro04CartonSNPlan:
    prefix = (getattr(product, "carton_id_prefix", None) or "").strip().upper()
    if prefix not in {"H", "K"}:
        raise HTTPException(status_code=400, detail="Erro 04 Product requires carton_id_prefix H or K.")

    now = printed_at or datetime.now()
    sequence = next_erro_04_sequence(db, year=now.year, lock=lock)
    return Erro04CartonSNPlan(
        carton_sn=f"{prefix}{pd027032_date_code(now)}{format_erro_04_sequence(sequence)}",
        sequence=sequence,
        date_code=now.strftime("%y%m%d"),
        carton_id_prefix=prefix,
    )
