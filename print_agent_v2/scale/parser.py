"""Parser module for OKS electronic weighing scale serial payloads."""

from dataclasses import dataclass
import re
from typing import Optional, Union

# Regex pattern matching optional sign, optional spaces, integer with optional decimal (dot or comma)
_WEIGHT_PATTERN: re.Pattern[str] = re.compile(
    r"(?P<weight>[+-]?\s*\d+(?:[.,]\d+)?)"
)


@dataclass(frozen=True)
class ScalePacketInfo:
    """Detailed parsing result containing numeric weight and status flags."""

    weight: str
    unit: str = "kg"
    is_stable: bool = True
    is_net: bool = False
    is_tare: bool = False
    is_zero: bool = False
    is_hold: bool = False


def parse_scale_packet_with_reason(
    data: Union[bytes, str],
) -> tuple[Optional[ScalePacketInfo], Optional[str]]:
    """Parse raw bytes or string into a structured ScalePacketInfo object and return reason if invalid."""
    if not data:
        return None, "Empty payload"

    if isinstance(data, bytes):
        try:
            text: str = data.decode("ascii", errors="ignore")
        except Exception as e:
            return None, f"Decode error: {e}"
    else:
        text = str(data)

    # Clean leading STX (0x02), trailing CRLF, and spaces
    cleaned_text: str = text.replace("\x02", "").strip()
    if not cleaned_text:
        return None, "Empty after stripping control characters"

    upper_text: str = cleaned_text.upper()

    # Reject non-weight lines: date/time keywords, AM/PM, ticket dividers, timestamps, ticket metadata
    if any(
        kw in upper_text
        for kw in (
            "DATE",
            "TIME",
            "YEAR",
            "MONTH",
            "DAY",
            "HOUR",
            "MIN",
            "SEC",
            "NO.",
            "NO:",
            "NUM",
            "TOTAL",
            "COUNT",
            "TICKET",
        )
    ):
        return None, "Non-weight header or divider"
    if re.search(r"\b(?:AM|PM)\b", upper_text):
        return None, "Non-weight timestamp (AM/PM)"
    if re.search(r"\d{2,4}[/-]\d{1,2}[/-]\d{2,4}", cleaned_text):
        return None, "Non-weight date format"
    if re.search(r"\d{1,2}:\d{2}(?::\d{2})?", cleaned_text):
        return None, "Non-weight time format"
    if all(c in "=-_*# \t" for c in cleaned_text):
        return None, "Non-weight separator line"

    # Must contain either scale indicator prefix, status flag, sign, or weight unit
    has_unit = "KG" in upper_text or "LB" in upper_text or bool(re.search(r"\b[GGT]\b", upper_text)) or " G" in upper_text
    has_scale_flag = any(
        flag in upper_text
        for flag in ("ST", "US", "GS", "NT", "PT", "WT", "WN", "GROSS", "NET", "TARE", "HOLD", "ZERO")
    )
    has_sign = "+" in cleaned_text or "-" in cleaned_text

    if not (has_unit or has_scale_flag or has_sign):
        return None, "Missing scale indicator, unit, or sign"

    # Strip leading sample/item counter prefix (e.g. 'n001', 'N 002', '#001', 'No.001')
    weight_search_text: str = re.sub(
        r"^(?:[nN]|#|NO\.?|NUM)\s*\d+\s*", "", cleaned_text, flags=re.IGNORECASE
    ).strip()
    if not weight_search_text:
        weight_search_text = cleaned_text

    match: Optional[re.Match[str]] = _WEIGHT_PATTERN.search(weight_search_text)
    if not match:
        return None, "Numeric weight pattern not found"

    weight_str: str = match.group("weight")
    normalized: str = re.sub(r"\s+", "", weight_str)
    if normalized.startswith("+"):
        normalized = normalized[1:]

    # Check for unit
    unit: str = "kg"
    if "G" in upper_text and "KG" not in upper_text:
        unit = "g"
    elif "LB" in upper_text:
        unit = "lb"

    # Status indicators
    is_stable: bool = True
    if "US" in upper_text or "UNSTABLE" in upper_text:
        is_stable = False

    is_net: bool = "NT" in upper_text or "NET" in upper_text
    is_tare: bool = "PT" in upper_text or is_net
    is_hold: bool = "HOLD" in upper_text

    try:
        val_float: float = float(normalized.replace(",", "."))
        is_zero: bool = abs(val_float) < 1e-6
    except ValueError:
        is_zero = False

    return (
        ScalePacketInfo(
            weight=normalized,
            unit=unit,
            is_stable=is_stable,
            is_net=is_net,
            is_tare=is_tare,
            is_zero=is_zero,
            is_hold=is_hold,
        ),
        None,
    )


def parse_scale_packet(data: Union[bytes, str]) -> Optional[ScalePacketInfo]:
    """Parse raw bytes or string into a structured ScalePacketInfo object."""
    info, _ = parse_scale_packet_with_reason(data)
    return info


def parse_weight_packet(data: Union[bytes, str]) -> Optional[str]:
    """Parse raw bytes or string received from scale and return weight string."""
    info = parse_scale_packet(data)
    return info.weight if info is not None else None
