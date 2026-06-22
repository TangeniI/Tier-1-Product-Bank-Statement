"""Unit tests for the reconciliation logic, independent of PDF parsing."""
from app.parser import RawRow
from app.reconcile import reconcile


def _txn(date, desc, out=None, inn=None, bal=None):
    return RawRow(date, date, desc, out, inn, bal, "txn")


def test_clean_chain_fully_reconciles():
    rows = [
        RawRow(None, "", "", None, None, 100000, "opening"),  # £1000
        _txn("2026-04-02", "A", out=4550, bal=95450),
        _txn("2026-04-05", "B", inn=200000, bal=295450),
    ]
    txns, summary, confidence = reconcile(rows)
    assert summary.flagged_rows == 0
    assert summary.opening_balance == 1000.00
    assert summary.balanced is True
    assert confidence == 1.0
    assert all(t.reconciled for t in txns)


def test_broken_row_is_flagged_not_fixed():
    rows = [
        RawRow(None, "", "", None, None, 100000, "opening"),
        _txn("2026-04-02", "A", out=4550, bal=95450),
        _txn("2026-04-03", "ATM withdrawal", out=10000, bal=84450),  # should be 85450
        _txn("2026-04-04", "C", inn=1000, bal=85450),  # reconciles vs stated prev
    ]
    txns, summary, confidence = reconcile(rows)
    assert summary.flagged_rows == 1
    flagged = [t for t in txns if not t.reconciled]
    assert len(flagged) == 1
    assert flagged[0].description == "ATM withdrawal"
    assert flagged[0].flag_reason and "off by" in flagged[0].flag_reason
    assert 0.6 < confidence < 0.7  # 2 of 3 checkable


def test_backcomputes_opening_when_no_anchor():
    rows = [
        _txn("2026-04-02", "A", out=4550, bal=95450),
        _txn("2026-04-05", "B", inn=200000, bal=295450),
    ]
    _txns, summary, _confidence = reconcile(rows)
    assert summary.opening_balance == 1000.00
    assert summary.flagged_rows == 0


def test_backcomputed_first_row_not_counted_in_confidence():
    # With no opening anchor, row 0 ties out by construction. Only row 1 is a
    # real check, so a single clean second row → full confidence (not "2/2"
    # where one was free).
    rows = [
        _txn("2026-04-02", "A", out=4550, bal=95450),
        _txn("2026-04-05", "B", inn=200000, bal=295450),
    ]
    _txns, _summary, confidence = reconcile(rows)
    assert confidence == 1.0

    # And a broken second row against a back-computed opening is 0/1, not 1/2.
    broken = [
        _txn("2026-04-02", "A", out=4550, bal=95450),
        _txn("2026-04-05", "B", inn=200000, bal=999999),  # wrong
    ]
    _t, _s, conf2 = reconcile(broken)
    assert conf2 == 0.0
