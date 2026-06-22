"""Running-balance reconciliation + confidence scoring.

This is the product's accuracy story and trust badge: for every transaction we
assert `previous_balance + money_in - money_out == stated_balance`. Rows that
break the chain are flagged (not silently "fixed"), and the overall confidence
is the share of checkable rows that reconcile. All arithmetic is in integer
pence.
"""
from __future__ import annotations

from typing import Optional

from .config import RECONCILE_TOLERANCE_PENCE
from .normalize import pence_to_pounds
from .parser import RawRow
from .schema import ReconcileSummary, Transaction


def _movement(row: RawRow) -> int:
    return (row.money_in or 0) - (row.money_out or 0)


def reconcile(
    raw_rows: list[RawRow], tolerance_pence: int = RECONCILE_TOLERANCE_PENCE
) -> tuple[list[Transaction], ReconcileSummary, float]:
    txns = [r for r in raw_rows if r.kind == "txn"]
    opening_row = next((r for r in raw_rows if r.kind == "opening"), None)
    closing_row = next((r for r in raw_rows if r.kind == "closing"), None)

    # Establish the opening balance to anchor the chain.
    opening: Optional[int] = None
    opening_backcomputed = False
    if opening_row is not None:
        opening = opening_row.balance
    elif txns and txns[0].balance is not None:
        # Back-compute the opening from the first row's stated balance. This
        # makes the first row reconcile by construction, so it is NOT an
        # independent check — we exclude it from the confidence denominator.
        opening = txns[0].balance - _movement(txns[0])
        opening_backcomputed = True

    out_rows: list[Transaction] = []
    prev: Optional[int] = opening
    checkable = 0
    reconciled_count = 0

    for idx, row in enumerate(txns):
        movement = _movement(row)
        reconciled = True
        flag: Optional[str] = None
        balance = row.balance

        if balance is None:
            # Statement should print a balance; infer it but flag for review.
            if prev is not None:
                balance = prev + movement
                reconciled = False
                flag = "Balance not printed — inferred from running total"
            prev = balance
        elif prev is None:
            # No anchor yet: first row sets the baseline, nothing to verify.
            prev = balance
        else:
            expected = prev + movement
            # The back-computed opening guarantees row 0 ties out; don't let that
            # synthetic pass inflate confidence.
            counts = not (opening_backcomputed and idx == 0)
            if counts:
                checkable += 1
            if abs(expected - balance) <= tolerance_pence:
                if counts:
                    reconciled_count += 1
            else:
                reconciled = False
                diff = pence_to_pounds(balance - expected)
                exp = pence_to_pounds(expected)
                flag = (
                    f"Running balance off by £{diff:+.2f} "
                    f"(expected £{exp:.2f}, statement shows £{pence_to_pounds(balance):.2f})"
                )
            prev = balance  # continue from the stated balance, not our guess

        out_rows.append(
            Transaction(
                date=row.date_iso or row.date_raw,
                description=row.description,
                money_in=pence_to_pounds(row.money_in),
                money_out=pence_to_pounds(row.money_out),
                balance=pence_to_pounds(balance),
                reconciled=reconciled,
                flag_reason=flag,
            )
        )

    # Closing reconciliation.
    stated_closing = (
        closing_row.balance
        if closing_row is not None
        else (txns[-1].balance if txns and txns[-1].balance is not None else None)
    )
    computed_closing = None
    if opening is not None:
        computed_closing = opening + sum(_movement(r) for r in txns)
    balanced = (
        stated_closing is not None
        and computed_closing is not None
        and abs(stated_closing - computed_closing) <= tolerance_pence
    )

    flagged_rows = sum(1 for t in out_rows if not t.reconciled)
    summary = ReconcileSummary(
        total_rows=len(out_rows),
        movement_rows=len(txns),
        reconciled_rows=len(out_rows) - flagged_rows,
        flagged_rows=flagged_rows,
        opening_balance=pence_to_pounds(opening),
        closing_balance=pence_to_pounds(stated_closing),
        computed_closing=pence_to_pounds(computed_closing),
        balanced=balanced,
    )

    confidence = _confidence(checkable, reconciled_count, len(out_rows), balanced)
    return out_rows, summary, confidence


def _confidence(
    checkable: int, reconciled_count: int, total_rows: int, balanced: bool
) -> float:
    if total_rows == 0:
        return 0.0
    if checkable == 0:
        # We extracted rows but had nothing to verify against (no anchor).
        return 0.3
    ratio = reconciled_count / checkable
    # Small bonus when the end-to-end opening→closing also ties out.
    if balanced and ratio >= 0.999:
        return 1.0
    return round(min(ratio, 0.99), 4)
