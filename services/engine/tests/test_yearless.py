"""Finding A: statements that print yearless dates ("02 Apr") must still parse,
with the year resolved from the statement period — including the Dec→Jan
boundary where the month decides the year."""
from make_fixture import BOUNDARY_EXPECTED_DATES, EXPECTED

from app.normalize import dominant_year, extract_statement_period, parse_date
from app.pipeline import extract


def test_extract_statement_period():
    text = "Statement of account · 01 Apr 2026 to 30 Apr 2026"
    assert extract_statement_period(text) == ("2026-04-01", "2026-04-30")


def test_extract_statement_period_long_form():
    text = "Statement period: 1 January 2026 - 31 January 2026"
    assert extract_statement_period(text) == ("2026-01-01", "2026-01-31")


def test_parse_date_yearless_uses_period():
    fmts = ("%d %b %Y", "%d %b")
    period = ("2026-04-01", "2026-04-30")
    assert parse_date("02 Apr", fmts, period=period) == "2026-04-02"


def test_parse_date_yearless_boundary():
    # Statement spans Dec 2025 → Jan 2026: month picks the year.
    fmts = ("%d %b",)
    period = ("2025-12-15", "2026-01-14")
    assert parse_date("20 Dec", fmts, period=period) == "2025-12-20"
    assert parse_date("05 Jan", fmts, period=period) == "2026-01-05"


def test_parse_date_yearless_without_context_returns_none():
    # No period, no default year → refuse to guess.
    assert parse_date("02 Apr", ("%d %b",)) is None


def test_parse_date_yearless_default_year():
    assert parse_date("02 Apr", ("%d %b",), default_year=2024) == "2024-04-02"


def test_dominant_year():
    assert dominant_year("paid 02 Apr 2026 and 05 Apr 2026, ref 1999") == 2026


def test_yearless_statement_matches_year_bearing_result(barclays_yearless_pdf_bytes):
    result = extract(barclays_yearless_pdf_bytes)
    # Same reconciliation outcome as the year-bearing fixture.
    assert len(result.rows) == EXPECTED["row_count"]
    assert result.summary.flagged_rows == EXPECTED["flagged_count"]
    # Every date resolved to the period's year.
    assert all(r.date.startswith("2026-") for r in result.rows)
    assert result.rows[0].date == "2026-04-02"


def test_boundary_statement_resolves_both_years(barclays_boundary_pdf_bytes):
    result = extract(barclays_boundary_pdf_bytes)
    dates = [r.date for r in result.rows]
    assert dates == BOUNDARY_EXPECTED_DATES
