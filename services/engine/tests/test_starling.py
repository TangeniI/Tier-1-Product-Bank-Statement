"""Second bank, structurally different layout: a single signed Amount column.
Proves the engine handles new banks via a profile (data), not parser changes."""
from make_fixture import STARLING_EXPECTED

from app.pipeline import extract


def test_starling_single_amount_column(starling_pdf_bytes):
    result = extract(starling_pdf_bytes)
    assert result.bank_profile == STARLING_EXPECTED["bank_profile"]
    assert len(result.rows) == STARLING_EXPECTED["row_count"]
    assert result.summary.opening_balance == STARLING_EXPECTED["opening_balance"]
    assert result.summary.closing_balance == STARLING_EXPECTED["closing_balance"]
    assert result.summary.balanced is STARLING_EXPECTED["balanced"]
    assert result.summary.flagged_rows == STARLING_EXPECTED["flagged_count"]


def test_starling_amount_split_into_in_out(starling_pdf_bytes):
    result = extract(starling_pdf_bytes)
    tesco = next(r for r in result.rows if "TESCO" in r.description)
    assert tesco.money_out == 45.50 and tesco.money_in is None
    salary = next(r for r in result.rows if "Salary" in r.description)
    assert salary.money_in == 2000.00 and salary.money_out is None


def test_starling_yearless_dates_resolved(starling_pdf_bytes):
    result = extract(starling_pdf_bytes)
    assert all(r.date.startswith("2026-05-") for r in result.rows)
