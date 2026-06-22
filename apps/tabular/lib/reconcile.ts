// Client-side running-balance reconciliation — mirrors
// services/engine/app/reconcile.py so the trust signals (per-row flags,
// summary, confidence) stay live and honest as the user edits cells.
//
// The product's promise is "every row is verified against the statement's own
// running balance." That verification must therefore re-run on every edit, not
// be frozen at extraction time. All arithmetic is in integer pence to stay
// exact, exactly like the engine.

import type { ReconcileSummary, Transaction } from "@/lib/types";

// Matches ENGINE_RECONCILE_TOLERANCE_PENCE (1p) in services/engine/app/config.py.
const TOLERANCE_PENCE = 1;

function toPence(pounds: number | null): number | null {
  return pounds == null ? null : Math.round(pounds * 100);
}

function toPounds(pence: number | null): number | null {
  return pence == null ? null : Math.round(pence) / 100;
}

function movementPence(t: Transaction): number {
  return (toPence(t.money_in) ?? 0) - (toPence(t.money_out) ?? 0);
}

export interface ReconcileResult {
  rows: Transaction[];
  summary: ReconcileSummary;
  confidence: number;
}

/**
 * Re-derive reconciliation for the (possibly edited) rows.
 *
 * `anchorOpening` is the opening balance established at extraction time (from
 * the statement's "balance brought forward" line). When absent we back-compute
 * it from the first row, mirroring the engine.
 */
export function reconcile(
  rows: Transaction[],
  anchorOpening: number | null,
): ReconcileResult {
  let opening = toPence(anchorOpening);
  const first = rows[0];
  let openingBackcomputed = false;
  if (opening == null && first != null && first.balance != null) {
    opening = (toPence(first.balance) ?? 0) - movementPence(first);
    openingBackcomputed = true;
  }

  const out: Transaction[] = [];
  let prev: number | null = opening;
  let checkable = 0;
  let reconciledCount = 0;

  for (let idx = 0; idx < rows.length; idx++) {
    const row = rows[idx]!;
    const movement = movementPence(row);
    let reconciled = true;
    let flag: string | null = null;
    let balance = toPence(row.balance);

    if (balance == null) {
      if (prev != null) {
        balance = prev + movement;
        reconciled = false;
        flag = "Balance not printed — inferred from running total";
      }
      prev = balance;
    } else if (prev == null) {
      // No anchor yet: first row sets the baseline, nothing to verify.
      prev = balance;
    } else {
      const expected = prev + movement;
      // The back-computed opening guarantees row 0 ties out; don't let that
      // synthetic pass inflate confidence.
      const counts = !(openingBackcomputed && idx === 0);
      if (counts) checkable += 1;
      if (Math.abs(expected - balance) <= TOLERANCE_PENCE) {
        if (counts) reconciledCount += 1;
      } else {
        reconciled = false;
        const diff = toPounds(balance - expected)!;
        const exp = toPounds(expected)!;
        const sign = diff >= 0 ? "+" : "";
        flag =
          `Running balance off by £${sign}${diff.toFixed(2)} ` +
          `(expected £${exp.toFixed(2)}, statement shows £${toPounds(balance)!.toFixed(2)})`;
      }
      prev = balance; // continue from the stated balance, not our guess
    }

    out.push({ ...row, balance: toPounds(balance), reconciled, flag_reason: flag });
  }

  const last = rows[rows.length - 1];
  const statedClosing = last ? toPence(last.balance) : null;
  const computedClosing =
    opening != null
      ? opening + rows.reduce((acc, r) => acc + movementPence(r), 0)
      : null;
  const balanced =
    statedClosing != null &&
    computedClosing != null &&
    Math.abs(statedClosing - computedClosing) <= TOLERANCE_PENCE;

  const flaggedRows = out.filter((t) => !t.reconciled).length;
  const summary: ReconcileSummary = {
    total_rows: out.length,
    movement_rows: out.length,
    reconciled_rows: out.length - flaggedRows,
    flagged_rows: flaggedRows,
    opening_balance: toPounds(opening),
    closing_balance: toPounds(statedClosing),
    computed_closing: toPounds(computedClosing),
    balanced,
  };

  return { rows: out, summary, confidence: confidence(checkable, reconciledCount, out.length, balanced) };
}

function confidence(
  checkable: number,
  reconciledCount: number,
  totalRows: number,
  balanced: boolean,
): number {
  if (totalRows === 0) return 0;
  if (checkable === 0) return 0.3;
  const ratio = reconciledCount / checkable;
  if (balanced && ratio >= 0.999) return 1;
  return Math.round(Math.min(ratio, 0.99) * 10000) / 10000;
}
