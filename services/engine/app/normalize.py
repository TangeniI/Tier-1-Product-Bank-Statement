"""Robust parsing of dates and money amounts into normalised internal forms.

Money is parsed to **signed integer pence** so all downstream arithmetic
(reconciliation especially) is exact. Pounds floats are only produced at the
very edge, for the API/exports.
"""
from __future__ import annotations

import re
from datetime import date, datetime
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


def _format_has_year(fmt: str) -> bool:
    return "%Y" in fmt or "%y" in fmt


def _resolve_year(
    month: int,
    day: int,
    period: Optional[tuple[str, str]],
    default_year: Optional[int],
) -> Optional[int]:
    """Pick the calendar year for a yearless (day, month) transaction date.

    Real statements print "02 Apr" and leave the year to the statement period
    header. We resolve it from that period — crucially handling the Dec→Jan
    boundary, where a statement running e.g. 15 Dec 2025 → 14 Jan 2026 contains
    both years and the month decides which one applies.
    """
    if period is not None:
        try:
            start = date.fromisoformat(period[0])
            end = date.fromisoformat(period[1])
        except (ValueError, TypeError):
            start = end = None
        if start and end:
            # Try every year spanned by the period and keep the candidate that
            # actually falls inside it; this resolves the year-boundary case.
            for yr in range(start.year, end.year + 1):
                try:
                    cand = date(yr, month, day)
                except ValueError:
                    continue
                if start <= cand <= end:
                    return yr
            # No exact fit (e.g. statement lists a date just outside the stated
            # period) — fall back to the end year, the safer assumption.
            return end.year
    return default_year


def parse_date(
    raw: str,
    formats: tuple[str, ...],
    period: Optional[tuple[str, str]] = None,
    default_year: Optional[int] = None,
) -> Optional[str]:
    """Parse a date string against the profile's formats → ISO YYYY-MM-DD.

    Year-bearing formats parse directly. For yearless formats ("%d %b") the year
    is resolved from the statement `period` (preferred) or a `default_year`. If
    neither is available we return None rather than guess a wrong year.
    """
    s = raw.strip()
    if not s:
        return None
    for fmt in formats:
        try:
            parsed = datetime.strptime(s, fmt).date()
        except ValueError:
            continue
        if _format_has_year(fmt):
            return parsed.isoformat()
        year = _resolve_year(parsed.month, parsed.day, period, default_year)
        if year is None:
            return None
        try:
            return date(year, parsed.month, parsed.day).isoformat()
        except ValueError:
            return None
    return None


# Statement-period phrases like "01 Apr 2026 to 30 Apr 2026" or
# "Statement period: 1 January 2026 - 31 January 2026". Two year-bearing dates
# joined by to/until/-/– give us the span the transactions live in.
_PERIOD_DATE = r"(\d{1,2}[ /]\w+[ /]\d{2,4}|\d{1,2}/\d{1,2}/\d{2,4})"
_PERIOD_RE = re.compile(
    rf"{_PERIOD_DATE}\s*(?:to|until|[-–—])\s*{_PERIOD_DATE}",
    re.IGNORECASE,
)
_PERIOD_FORMATS = (
    "%d %b %Y", "%d %B %Y", "%d %b %y", "%d/%m/%Y", "%d/%m/%y",
)


def extract_statement_period(text: str) -> Optional[tuple[str, str]]:
    """Find the statement's date span (ISO start, ISO end) from its header text."""
    for m in _PERIOD_RE.finditer(text):
        start = _try_formats(m.group(1).strip(), _PERIOD_FORMATS)
        end = _try_formats(m.group(2).strip(), _PERIOD_FORMATS)
        if start and end and start <= end:
            return (start, end)
    return None


def _try_formats(s: str, formats: tuple[str, ...]) -> Optional[str]:
    for fmt in formats:
        try:
            return datetime.strptime(s, fmt).date().isoformat()
        except ValueError:
            continue
    return None


def dominant_year(text: str) -> Optional[int]:
    """Most frequent 4-digit year in the document — a fallback when no explicit
    statement period is present."""
    full = [int(y) for y in re.findall(r"\b((?:19|20)\d{2})\b", text)]
    if not full:
        return None
    return max(set(full), key=full.count)


def pence_to_pounds(pence: Optional[int]) -> Optional[float]:
    if pence is None:
        return None
    return round(pence / 100, 2)


def pounds_to_pence(pounds: Optional[float]) -> Optional[int]:
    if pounds is None:
        return None
    return int((Decimal(str(pounds)) * 100).quantize(Decimal("1"), rounding=ROUND_HALF_UP))
