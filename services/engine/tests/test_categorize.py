"""Keyword categorisation gives a sensible first pass; duplicates are flagged."""
from app.categorize import categorize
from app.pipeline import _count_duplicates
from app.schema import Transaction


def test_categorize_known_merchants():
    assert categorize("Card payment to TESCO STORES") == "Groceries & Supplies"
    assert categorize("Salary ACME LTD") == "Income / Sales"
    assert categorize("Direct debit BRITISH GAS ENERGY") == "Utilities"
    assert categorize("HMRC VAT payment") == "Tax & HMRC"
    assert categorize("ATM withdrawal") == "Travel & Transport"


def test_categorize_unknown_is_none():
    assert categorize("Mysterious counterparty xyz") is None
    assert categorize("") is None


def test_duplicate_detection():
    rows = [
        Transaction(date="2026-04-02", description="TESCO", money_out=45.50),
        Transaction(date="2026-04-02", description="tesco", money_out=45.50),  # dup
        Transaction(date="2026-04-03", description="TESCO", money_out=45.50),  # not
    ]
    assert _count_duplicates(rows) == 1
