from dataclasses import dataclass

from sqlalchemy.orm import Session

from src.core import models

DEFAULT_SSCC_COMPANY_PREFIX = "37033907"
SSCC_SEQUENCE_WIDTH = 7


@dataclass(frozen=True)
class SSCCCartonPlan:
    company_prefix: str
    sequence: int
    check_digit: int
    carton_sn: str
    sscc_text: str


def calculate_gs1_check_digit(number_str: str) -> int:
    """
    Calculates standard GS1 Modulo 10 check digit for any numeric string (SSCC, GTIN, UPC).
    Iterates digits from right to left with weights 3, 1, 3, 1...
    """
    clean_str = "".join(c for c in str(number_str) if c.isdigit())
    if not clean_str:
        return 0
    total = 0
    weights = [3, 1]
    for i, char in enumerate(reversed(clean_str)):
        weight = weights[i % 2]
        total += int(char) * weight
    remainder = total % 10
    return 0 if remainder == 0 else (10 - remainder)


def format_sscc_18(company_prefix: str, sequence: int) -> str:
    """
    Constructs full 18-digit SSCC string:
    '0' + company_prefix + sequence(7 digits) + check_digit(1 digit)
    """
    clean_prefix = "".join(c for c in company_prefix if c.isdigit()) or DEFAULT_SSCC_COMPANY_PREFIX
    seq_str = str(sequence).zfill(SSCC_SEQUENCE_WIDTH)
    data_17 = f"0{clean_prefix}{seq_str}"
    cd = calculate_gs1_check_digit(data_17)
    return f"{data_17}{cd}"


def format_sscc_display_text(company_prefix: str, sequence: int) -> str:
    """
    Formats the human-readable text on label:
    '(00) 0 {company_prefix} {seq:07d}'
    """
    clean_prefix = "".join(c for c in company_prefix if c.isdigit()) or DEFAULT_SSCC_COMPANY_PREFIX
    seq_str = str(sequence).zfill(SSCC_SEQUENCE_WIDTH)
    return f"(00) 0 {clean_prefix} {seq_str}"


def parse_sscc_sequence(carton_sn: str | None, company_prefix: str = DEFAULT_SSCC_COMPANY_PREFIX) -> int:
    """
    Extracts the 7-digit sequence number from an 18-digit SSCC string.
    Format: 0 + company_prefix(8) + sequence(7) + check_digit(1)
    """
    if not carton_sn:
        return 0
    clean_sn = "".join(c for c in carton_sn if c.isdigit())
    clean_prefix = "".join(c for c in company_prefix if c.isdigit())
    prefix_with_lead = f"0{clean_prefix}"
    if not clean_sn.startswith(prefix_with_lead) or len(clean_sn) != (1 + len(clean_prefix) + SSCC_SEQUENCE_WIDTH + 1):
        return 0
    
    seq_part = clean_sn[len(prefix_with_lead) : len(prefix_with_lead) + SSCC_SEQUENCE_WIDTH]
    try:
        return int(seq_part)
    except ValueError:
        return 0


def next_sscc_sequence(db: Session, company_prefix: str = DEFAULT_SSCC_COMPANY_PREFIX, lock: bool = False) -> int:
    """
    Finds the maximum sequence allocated globally for the given company_prefix.
    Sequence starts from 1 (0000001) and increments monotonically, never resetting.
    """
    clean_prefix = "".join(c for c in company_prefix if c.isdigit()) or DEFAULT_SSCC_COMPANY_PREFIX
    lead_prefix = f"0{clean_prefix}"

    if lock:
        # Multiple Erro 02 Products may share one GS1 company prefix. Lock the
        # full namespace rather than only the selected Product.
        (
            db.query(models.Product.id)
            .filter(
                models.Product.template_type == "erro_02",
                models.Product.pkg_prefix == clean_prefix,
            )
            .with_for_update()
            .all()
        )

    query = db.query(models.Carton.carton_sn).filter(
        models.Carton.carton_sn.like(f"{lead_prefix}%"),
        models.Carton.is_reprint == 0,
    )
    if lock:
        query = query.with_for_update()

    rows = query.all()
    if not rows:
        return 1

    max_seq = 0
    for r in rows:
        seq = parse_sscc_sequence(r[0], clean_prefix)
        max_seq = max(max_seq, seq)

    return max_seq + 1


def plan_next_sscc_carton_sn(
    db: Session,
    product: models.Product,
    custom_sequence: int | None = None,
    lock: bool = False,
) -> SSCCCartonPlan:
    """
    Allocates the next SSCC carton SN and display text plan for a product.
    """
    company_prefix = getattr(product, 'pkg_prefix', None) or DEFAULT_SSCC_COMPANY_PREFIX
    clean_prefix = "".join(c for c in company_prefix if c.isdigit()) or DEFAULT_SSCC_COMPANY_PREFIX

    if custom_sequence is not None and custom_sequence > 0:
        sequence = custom_sequence
    else:
        sequence = next_sscc_sequence(db, clean_prefix, lock=lock)

    carton_sn = format_sscc_18(clean_prefix, sequence)
    cd = int(carton_sn[-1])
    sscc_text = format_sscc_display_text(clean_prefix, sequence)

    return SSCCCartonPlan(
        company_prefix=clean_prefix,
        sequence=sequence,
        check_digit=cd,
        carton_sn=carton_sn,
        sscc_text=sscc_text,
    )
