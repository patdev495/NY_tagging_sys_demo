import datetime
import re
from dataclasses import dataclass

from sqlalchemy.orm import Session

from src.core import models

ERRO_01_SEQUENCE_WIDTH = 6


@dataclass(frozen=True)
class Erro01CartonSNPlan:
    prefix: str
    yymm: str
    sequence: int
    carton_sn: str
    date_code: str




def current_iso_date_code() -> str:
    """Returns ISO Date Code in standard YYWW format (e.g., 2634 for Week 34 of 2026)."""
    now = datetime.datetime.now()
    yy = now.strftime("%y")
    ww = f"{now.isocalendar()[1]:02d}"
    return f"{yy}{ww}"


def current_yymm() -> str:
    return datetime.datetime.now().strftime("%y%m")


def format_erro_01_carton_sn(pkg_prefix: str, yymm: str, sequence: int) -> str:
    return f"{pkg_prefix}{yymm}{str(sequence).zfill(ERRO_01_SEQUENCE_WIDTH)}"


def parse_erro_01_sequence(carton_sn: str | None) -> int:
    if not carton_sn:
        return 0
    sequence_text = carton_sn[-ERRO_01_SEQUENCE_WIDTH:]
    if not re.fullmatch(r"\d+", sequence_text):
        return 0
    try:
        return int(sequence_text)
    except ValueError:
        return 0


def next_erro_01_sequence(
    db: Session,
    pkg_prefix: str,
    yy: str,
    lock: bool = False,
    product_id: int | None = None,
) -> int:
    """
    Finds the maximum sequence allocated in the given year (YY) for the specified Product and pkg_prefix.
    """
    filters = [
        models.Carton.carton_sn.like(f"{pkg_prefix}{yy}%"),
        models.Carton.is_reprint == 0,
    ]
    if product_id is not None:
        filters.append(models.Carton.product_id == product_id)

    query = db.query(models.Carton.carton_sn).filter(*filters)
    if lock:
        query = query.with_for_update()
    
    rows = query.all()
    if not rows:
        return 1
    
    max_seq = max(parse_erro_01_sequence(r[0]) for r in rows)
    return max_seq + 1


def plan_next_erro_01_carton_sn(
    db: Session,
    product: models.Product,
    custom_yymm: str | None = None,
    custom_sequence: int | None = None,
    lock: bool = False,
) -> Erro01CartonSNPlan:
    raw_prefix = getattr(product, "pkg_prefix", None) or getattr(product, "start_part", None) or "VHK0010237"
    pkg_prefix: str = str(raw_prefix)
    yymm = custom_yymm or current_yymm()
    yy = yymm[:2]
    raw_id = getattr(product, "id", None)
    prod_id: int | None = int(raw_id) if raw_id is not None else None
    
    if custom_sequence is not None and custom_sequence > 0:
        sequence = custom_sequence
    else:
        sequence = next_erro_01_sequence(
            db,
            pkg_prefix=pkg_prefix,
            yy=yy,
            lock=lock,
            product_id=prod_id,
        )

    carton_sn = format_erro_01_carton_sn(pkg_prefix, yymm, sequence)
    date_code = current_iso_date_code()
    
    return Erro01CartonSNPlan(
        prefix=pkg_prefix,
        yymm=yymm,
        sequence=sequence,
        carton_sn=carton_sn,
        date_code=date_code,
    )
