"""End-to-end: synthetic Barclays PDF → ExtractionResult, against EXPECTED."""
from make_fixture import EXPECTED

from app.pipeline import extract


def test_extract_barclays_fixture(barclays_pdf_bytes):
    result = extract(barclays_pdf_bytes)

    assert result.has_text_layer is True
    assert result.bank_profile == EXPECTED["bank_profile"]
    assert len(result.rows) == EXPECTED["row_count"]

    # Reconciliation summary.
    assert result.summary.opening_balance == EXPECTED["opening_balance"]
    assert result.summary.closing_balance == EXPECTED["closing_balance"]
    assert result.summary.computed_closing == EXPECTED["computed_closing"]
    assert result.summary.balanced is EXPECTED["balanced"]
    assert result.summary.flagged_rows == EXPECTED["flagged_count"]

    # The one bad row is flagged and correctly identified.
    flagged = [r for r in result.rows if not r.reconciled]
    assert len(flagged) == EXPECTED["flagged_count"]
    assert flagged[0].description == EXPECTED["flagged_description"]

    # Confidence reflects 6/7 checkable rows reconciling.
    assert abs(result.overall_confidence - EXPECTED["confidence_approx"]) < 0.01

    # Multi-line description was stitched back together.
    descriptions = [r.description for r in result.rows]
    assert EXPECTED["multiline_description"] in descriptions


def test_first_and_last_amounts(barclays_pdf_bytes):
    result = extract(barclays_pdf_bytes)
    first = result.rows[0]
    assert first.money_out == 45.50
    assert first.balance == 954.50

    salary = next(r for r in result.rows if "Salary" in r.description)
    assert salary.money_in == 2000.00
