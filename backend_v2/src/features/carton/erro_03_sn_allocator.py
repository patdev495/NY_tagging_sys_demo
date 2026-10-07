import datetime
from dataclasses import dataclass

from sqlalchemy.orm import Session

from src.core import models

DEFAULT_ERRO_03_SUPPLIER_CODE = "1012665"
ERRO_03_SEQUENCE_WIDTH = 4


@dataclass(frozen=True)
class Erro03CartonPlan:
    supplier_code: str
    yymmdd: str
    sequence: int
    carton_sn: str


def format_erro_03_carton_sn(supplier_code: str, yymmdd: str, sequence: int) -> str:
    """
    Constructs the full 17-character carton SN for Erro 03 (Luxshare NME):
    supplier_code(7 chars) + yymmdd(6 chars) + sequence(4 digits)
    Example: '1012665' + '260911' + '0001' = '10126652609110001'
    """
    clean_code = "".join(c for c in supplier_code if c.isdigit()) or DEFAULT_ERRO_03_SUPPLIER_CODE
    seq_str = str(sequence).zfill(ERRO_03_SEQUENCE_WIDTH)
    return f"{clean_code}{yymmdd}{seq_str}"


def parse_erro_03_sequence(carton_sn: str | None, supplier_code: str, yy_or_yymmdd: str) -> int:
    """
    Extracts the 4-digit sequence number from a 17-character Tem 3 carton SN for the given year (YY).
    Format: supplier_code(7) + yymmdd(6) + sequence(4)
    """
    if not carton_sn:
        return 0
    clean_sn = "".join(c for c in carton_sn if c.isdigit())
    clean_code = "".join(c for c in supplier_code if c.isdigit()) or DEFAULT_ERRO_03_SUPPLIER_CODE
    yy = yy_or_yymmdd[:2]
    prefix = f"{clean_code}{yy}"
    if not clean_sn.startswith(prefix) or len(clean_sn) != (len(clean_code) + 6 + ERRO_03_SEQUENCE_WIDTH):
        return 0

    seq_part = clean_sn[-ERRO_03_SEQUENCE_WIDTH:]
    try:
        return int(seq_part)
    except ValueError:
        return 0


def next_erro_03_sequence(
    db: Session,
    supplier_code: str,
    yy_or_yymmdd: str,
    lock: bool = False,
    product_id: int | None = None,
) -> int:
    """
    Finds the maximum sequence allocated in the given year (YY) for the specified supplier_code (and product).
    Sequence starts from 1 (0001) and resets yearly on January 1st.
    """
    clean_code = "".join(c for c in supplier_code if c.isdigit()) or DEFAULT_ERRO_03_SUPPLIER_CODE
    yy = yy_or_yymmdd[:2]
    lead_prefix = f"{clean_code}{yy}"

    filters = [
        models.Carton.carton_sn.like(f"{lead_prefix}%"),
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

    max_seq = 0
    for r in rows:
        seq = parse_erro_03_sequence(r[0], clean_code, yy)
        max_seq = max(max_seq, seq)

    return max_seq + 1


def plan_next_erro_03_carton_sn(
    db: Session,
    product: models.Product,
    custom_yymmdd: str | None = None,
    custom_sequence: int | None = None,
    lock: bool = False,
) -> Erro03CartonPlan:
    """
    Allocates the next Tem 3 carton SN plan for a product.
    Sequence resets yearly on January 1st.
    """
    raw_supplier = getattr(product, 'pkg_prefix', None) or DEFAULT_ERRO_03_SUPPLIER_CODE
    clean_code = "".join(c for c in str(raw_supplier) if c.isdigit()) or DEFAULT_ERRO_03_SUPPLIER_CODE

    if custom_yymmdd:
        yymmdd = custom_yymmdd
    else:
        now = datetime.datetime.now()
        yymmdd = now.strftime("%y%m%d")

    yy = yymmdd[:2]
    raw_id = getattr(product, "id", None)
    prod_id: int | None = int(raw_id) if raw_id is not None else None

    if custom_sequence is not None and custom_sequence > 0:
        sequence = custom_sequence
    else:
        sequence = next_erro_03_sequence(
            db,
            clean_code,
            yy,
            lock=lock,
            product_id=prod_id,
        )

    carton_sn = format_erro_03_carton_sn(clean_code, yymmdd, sequence)

    return Erro03CartonPlan(
        supplier_code=clean_code,
        yymmdd=yymmdd,
        sequence=sequence,
        carton_sn=carton_sn,
    )
