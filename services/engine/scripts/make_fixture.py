"""Generate a synthetic Barclays-style statement PDF for tests/demos.

We control the geometry so the layout exercises the real positional parser:
borderless columns, right-aligned money, a multi-line (wrapped) description, and
one deliberately NON-reconciling row so the flagging path is covered.

The canonical transaction data lives here too, so tests assert against the same
source of truth that drew the PDF.

Usage:
    python scripts/make_fixture.py [output.pdf]
"""
from __future__ import annotations

import sys
from pathlib import Path

# Column geometry (points, reportlab origin = bottom-left). Chosen so each
# column's words fall cleanly into the parser's x-bands.
DATE_X = 40  # left-aligned
DESC_X = 110  # left-aligned
OUT_RIGHT = 420  # right-aligned
IN_RIGHT = 490  # right-aligned
BAL_RIGHT = 560  # right-aligned

BANK_HEADER = "Barclays Bank UK PLC"
OPENING_BALANCE = "1,000.00"
CLOSING_BALANCE = "2,949.96"

# date, description, money_out, money_in, balance, continuation-line
TRANSACTIONS = [
    ("02 Apr 2026", "Card payment to TESCO STORES", "45.50", None, "954.50", None),
    ("05 Apr 2026", "Salary ACME LTD", None, "2,000.00", "2,954.50", None),
    ("09 Apr 2026", "Direct debit BRITISH GAS ENERGY", "120.00", None, "2,834.50", "monthly tariff"),
    ("12 Apr 2026", "Faster payment from J SMITH", None, "250.00", "3,084.50", None),
    ("15 Apr 2026", "Card payment to AMAZON UK", "33.99", None, "3,050.51", None),
    # Deliberately wrong: correct running balance would be 2,950.51.
    ("20 Apr 2026", "ATM withdrawal", "100.00", None, "2,949.51", None),
    ("25 Apr 2026", "Interest paid", None, "0.45", "2,949.96", None),
]

# What the engine should conclude — imported by tests.
EXPECTED = {
    "bank_profile": "barclays",
    "row_count": 7,
    "flagged_count": 1,
    "flagged_description": "ATM withdrawal",
    "opening_balance": 1000.00,
    "closing_balance": 2949.96,
    "computed_closing": 2950.96,
    "balanced": False,
    "confidence_approx": 0.857,
    "multiline_description": "Direct debit BRITISH GAS ENERGY monthly tariff",
}


# Yearless variant: identical statement, but the transaction dates omit the
# year (as most real Barclays statements do) — the year lives only in the
# period line. The engine must resolve every date to 2026 from that period.
PERIOD_LINE = "Statement of account · 01 Apr 2026 to 30 Apr 2026"
YEARLESS_TRANSACTIONS = [
    (d.replace(" 2026", ""), desc, out, inn, bal, cont)
    for (d, desc, out, inn, bal, cont) in TRANSACTIONS
]

# Year-boundary variant: a statement spanning Dec 2025 → Jan 2026 with yearless
# dates. December rows must resolve to 2025 and January rows to 2026.
BOUNDARY_PERIOD_LINE = "Statement of account · 15 Dec 2025 to 14 Jan 2026"
BOUNDARY_OPENING = "500.00"
BOUNDARY_CLOSING = "560.00"
BOUNDARY_TRANSACTIONS = [
    ("20 Dec", "Card payment to TESCO STORES", "40.00", None, "460.00", None),
    ("28 Dec", "Salary ACME LTD", None, "100.00", "560.00", None),
    ("05 Jan", "Interest paid", None, "0.00", "560.00", None),
]
BOUNDARY_EXPECTED_DATES = ["2025-12-20", "2025-12-28", "2026-01-05"]


def _draw_statement(c, height, period_line, opening, closing, transactions) -> None:
    c.setFont("Helvetica-Bold", 14)
    c.drawString(DATE_X, height - 50, BANK_HEADER)
    c.setFont("Helvetica", 9)
    c.drawString(DATE_X, height - 68, period_line)

    # Column headers.
    y = height - 110
    c.setFont("Helvetica-Bold", 9)
    c.drawString(DATE_X, y, "Date")
    c.drawString(DESC_X, y, "Description")
    c.drawRightString(OUT_RIGHT, y, "Money Out")
    c.drawRightString(IN_RIGHT, y, "Money In")
    c.drawRightString(BAL_RIGHT, y, "Balance")

    c.setFont("Helvetica", 9)
    y -= 22
    c.drawString(DESC_X, y, "Balance brought forward")
    c.drawRightString(BAL_RIGHT, y, opening)

    for date, desc, out, inn, bal, cont in transactions:
        y -= 18
        c.drawString(DATE_X, y, date)
        c.drawString(DESC_X, y, desc)
        if out:
            c.drawRightString(OUT_RIGHT, y, out)
        if inn:
            c.drawRightString(IN_RIGHT, y, inn)
        c.drawRightString(BAL_RIGHT, y, bal)
        if cont:
            y -= 12
            c.drawString(DESC_X, y, cont)

    y -= 18
    c.setFont("Helvetica-Bold", 9)
    c.drawString(DESC_X, y, "Balance carried forward")
    c.drawRightString(BAL_RIGHT, y, closing)


def _render(path: Path, period_line, opening, closing, transactions) -> None:
    from reportlab.lib.pagesizes import A4
    from reportlab.pdfgen import canvas

    _width, height = A4
    c = canvas.Canvas(str(path), pagesize=A4)
    _draw_statement(c, height, period_line, opening, closing, transactions)
    c.showPage()
    c.save()


def build_pdf(path: Path) -> None:
    """The canonical year-bearing fixture."""
    _render(path, PERIOD_LINE, OPENING_BALANCE, CLOSING_BALANCE, TRANSACTIONS)


def build_yearless_pdf(path: Path) -> None:
    """Same statement with yearless transaction dates."""
    _render(path, PERIOD_LINE, OPENING_BALANCE, CLOSING_BALANCE, YEARLESS_TRANSACTIONS)


def build_boundary_pdf(path: Path) -> None:
    """Yearless statement spanning the Dec→Jan year boundary."""
    _render(
        path,
        BOUNDARY_PERIOD_LINE,
        BOUNDARY_OPENING,
        BOUNDARY_CLOSING,
        BOUNDARY_TRANSACTIONS,
    )


if __name__ == "__main__":
    out = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("barclays_sample.pdf")
    build_pdf(out)
    print(f"Wrote {out}")
