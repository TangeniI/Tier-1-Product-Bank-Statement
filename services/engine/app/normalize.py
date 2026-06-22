"""Robust parsing of dates and money amounts into normalised internal forms.

Money is parsed to **signed integer pence** so all downstream arithmetic
(reconciliation especially) is exact. Pounds floats are only produced at the
very edge, for the API/exports.
"""
from __future__ import annotations

import re
from datetime import datetime
from decimal import ROUND_HALF_UP, Decimal
from typing import Optional

# Matches a currency-ish number, optionally parenthesised/negative, optionally
# trailed by CR/DR.
_AMOUNT_RE = re.compile(
    r"""
    ^\s*
    (?P<paren>\()?
    (?P<sign>[-+])?
    \s*£?\s*
    (?P<num>[\d,\s]*\d(?:\.\d{1,2})?)
    \)?
    \s*(?P<crdr>CR|DR)?
    \s*$
    """,
    re.IGNORECASE | re.VERBOSE,
)


def parse_amount(raw: str) -> Optional[int]:
    """Parse a money token to signed integer pence, or None if not a number.

    Handles: '£1,234.56', '1234.56', '(50.00)' → -5000, '-12.30', '45.00 CR',
    '45.00 DR' → -4500. Whitespace and thousands separators are stripped.
    """
    if raw is None:
        return None
    s = raw.strip()
    if not s:
        return None
    m = _AMOUNT_RE.match(s)
    if not m:
        return None
    num = m.group("num").replace(",", "").replace(" ", "")
    if not num:
        return None
    try:
        value = Decimal(num)
    except Exception:
        return None
    pence = int((value * 100).quantize(Decimal("1"), rounding=ROUND_HALF_UP))

    negative = False
    if m.group("paren"):
        negative = True
    if m.group("sign") == "-":
        negative = True
    crdr = (m.group("crdr") or "").upper()
    if crdr == "DR":
        negative = True
    return -pence if negative else pence


def looks_like_amount(token: str) -> bool:
    return parse_amount(token) is not None


def parse_date(raw: str, formats: tuple[str, ...]) -> Optional[str]:
    """Parse a date string against the profile's formats → ISO YYYY-MM-DD.

    For two-token-or-fewer day-month formats with no year, the year is left to
    the caller (we return None so the raw text is preserved instead of guessing).
    """
    s = raw.strip()
    if not s:
        return None
    for fmt in formats:
        try:
            return datetime.strptime(s, fmt).date().isoformat()
        except ValueError:
            continue
    return None


def pence_to_pounds(pence: Optional[int]) -> Optional[float]:
    if pence is None:
        return None
    return round(pence / 100, 2)


def pounds_to_pence(pounds: Optional[float]) -> Optional[int]:
    if pounds is None:
        return None
    return int((Decimal(str(pounds)) * 100).quantize(Decimal("1"), rounding=ROUND_HALF_UP))
