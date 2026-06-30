"use client";

import * as React from "react";
import { Badge, Button, ConfidenceBadge } from "@tabular/ui";
import { track } from "@tabular/analytics";
import type { ExtractionResult, Preset, Transaction } from "@/lib/types";
import { reconcile } from "@/lib/reconcile";
import { applyLearned, learn } from "@/lib/categoryMemory";

function money(n: number | null): string {
  return n == null ? "" : n.toFixed(2);
}

function parseMoney(v: string): number | null {
  const t = v.trim();
  if (t === "") return null;
  const n = Number(t.replace(/[£,\s]/g, ""));
  return Number.isFinite(n) ? n : null;
}

type EditableField =
  | "date"
  | "description"
  | "category"
  | "money_in"
  | "money_out"
  | "balance";

export function ResultsTable({ result }: { result: ExtractionResult }) {
  const [rows, setRows] = React.useState<Transaction[]>(result.rows);
  const [presets, setPresets] = React.useState<Preset[]>([
    { name: "default", label: "Tabular (all columns)" },
  ]);
  const [preset, setPreset] = React.useState("default");
  const [busy, setBusy] = React.useState(false);

  React.useEffect(() => {
    fetch("/api/export")
      .then((r) => r.json())
      .then((p: Preset[]) => {
        if (Array.isArray(p) && p.length) setPresets(p);
      })
      .catch(() => {});
  }, []);

  // On mount (client only), apply categories the user has taught in this
  // browser — their corrections override the engine's first-pass guesses.
  React.useEffect(() => {
    setRows((prev) => applyLearned(prev));
  }, []);

  function updateCell(i: number, field: EditableField, value: string) {
    setRows((prev) => {
      const next = [...prev];
      const row = { ...next[i] } as Transaction;
      if (field === "description" || field === "date") {
        row[field] = value;
      } else if (field === "category") {
        row.category = value.trim() === "" ? null : value;
        // Remember this correction for matching merchants, now and next time.
        learn(row.description, row.category);
      } else {
        row[field] = parseMoney(value);
      }
      next[i] = row;
      track({ name: "row_edited", props: {} });
      return next;
    });
  }

  async function doExport(format: "csv" | "xlsx" | "ofx") {
    setBusy(true);
    track({ name: "export_clicked", props: { format, preset } });
    try {
      const res = await fetch("/api/export", {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({ rows, format, preset, filename: "statement" }),
      });
      if (!res.ok) {
        alert("Export failed. Please try again.");
        return;
      }
      const blob = await res.blob();
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      // OFX carries its own transaction layout, independent of the CSV preset.
      a.download = format === "ofx" ? "statement.ofx" : `statement-${preset}.${format}`;
      document.body.appendChild(a);
      a.click();
      a.remove();
      URL.revokeObjectURL(url);
    } finally {
      setBusy(false);
    }
  }

  // Re-run reconciliation on every edit so the trust signals stay honest: the
  // opening balance from extraction anchors the chain, everything below is
  // recomputed from the (possibly edited) rows.
  const recon = React.useMemo(
    () => reconcile(rows, result.summary.opening_balance),
    [rows, result.summary.opening_balance],
  );
  const verified = recon.rows;
  const flaggedCount = recon.summary.flagged_rows;
  const s = recon.summary;

  // Autocomplete categories from whatever's already in use (engine + learned).
  const knownCategories = React.useMemo(
    () => [...new Set(rows.map((r) => r.category).filter(Boolean))] as string[],
    [rows],
  );

  return (
    <div className="space-y-5">
      {/* Summary / trust bar */}
      <div className="flex flex-wrap items-center gap-3 rounded-[10px] border border-[var(--tab-border)] bg-white p-4">
        <ConfidenceBadge score={recon.confidence} />
        <Badge tone="brand">{result.bank_profile}</Badge>
        <span className="text-sm text-gray-600">
          {s.movement_rows} transactions · {flaggedCount} to review
        </span>
        <span className="text-sm text-gray-600">
          Opening £{money(s.opening_balance)} → Closing £{money(s.closing_balance)}
        </span>
        <Badge tone={s.balanced ? "reconciled" : "flagged"}>
          {s.balanced ? "Balances to statement" : "Does not fully balance"}
        </Badge>
      </div>

      {result.warnings.length > 0 && (
        <div className="rounded-[10px] border border-amber-200 bg-amber-50 p-3 text-sm text-[var(--tab-flagged)]">
          {result.warnings.map((w, i) => (
            <p key={i}>{w}</p>
          ))}
        </div>
      )}

      {/* Export controls */}
      <div className="flex flex-wrap items-center gap-3">
        <label className="text-sm font-medium">Format for</label>
        <select
          value={preset}
          onChange={(e) => setPreset(e.target.value)}
          className="rounded-[8px] border border-[var(--tab-border)] bg-white px-3 py-2 text-sm"
        >
          {presets.map((p) => (
            <option key={p.name} value={p.name}>
              {p.label}
            </option>
          ))}
        </select>
        <Button onClick={() => doExport("csv")} disabled={busy}>
          Export CSV
        </Button>
        <Button variant="secondary" onClick={() => doExport("xlsx")} disabled={busy}>
          Export Excel
        </Button>
        <Button
          variant="secondary"
          onClick={() => doExport("ofx")}
          disabled={busy}
          title="OFX/QBO bank-feed file for QuickBooks, Xero and most accounting tools"
        >
          Export OFX / QBO
        </Button>
      </div>

      {/* Editable table */}
      <div className="overflow-x-auto rounded-[10px] border border-[var(--tab-border)] bg-white">
        <table className="w-full min-w-[960px] border-collapse text-sm">
          <colgroup>
            <col style={{ width: "116px" }} />
            <col style={{ minWidth: "200px" }} />
            <col style={{ width: "200px" }} />
            <col style={{ width: "108px" }} />
            <col style={{ width: "108px" }} />
            <col style={{ width: "120px" }} />
            <col style={{ width: "104px" }} />
          </colgroup>
          <thead>
            <tr className="border-b border-[var(--tab-border)] bg-[var(--tab-surface-muted)] text-left">
              <th scope="col" className="whitespace-nowrap px-3 py-2.5 font-medium">Date</th>
              <th scope="col" className="px-3 py-2.5 font-medium">Description</th>
              <th scope="col" className="px-3 py-2.5 font-medium">Category</th>
              <th scope="col" className="whitespace-nowrap px-3 py-2.5 text-right font-medium">Money in</th>
              <th scope="col" className="whitespace-nowrap px-3 py-2.5 text-right font-medium">Money out</th>
              <th scope="col" className="whitespace-nowrap px-3 py-2.5 text-right font-medium">Balance</th>
              <th scope="col" className="px-3 py-2.5 font-medium">Status</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((r, i) => {
              const v = verified[i] ?? r;
              const showReason = !v.reconciled && Boolean(v.flag_reason);
              return (
                <React.Fragment key={i}>
                  <tr
                    className={`${!v.reconciled ? "bg-amber-50" : ""} ${
                      showReason
                        ? ""
                        : "border-b border-[var(--tab-border)] last:border-0"
                    }`}
                  >
                    <Cell row={i} col="date" value={r.date} onChange={updateCell} />
                    <Cell row={i} col="description" value={r.description} onChange={updateCell} />
                    <Cell
                      row={i}
                      col="category"
                      value={r.category ?? ""}
                      onChange={updateCell}
                      placeholder="Uncategorised"
                      list="tab-categories"
                    />
                    <Cell row={i} col="money_in" value={money(r.money_in)} onChange={updateCell} align="right" />
                    <Cell row={i} col="money_out" value={money(r.money_out)} onChange={updateCell} align="right" />
                    <Cell row={i} col="balance" value={money(r.balance)} onChange={updateCell} align="right" />
                    <td className="px-3 py-1.5 align-middle">
                      {v.reconciled ? (
                        <Badge tone="reconciled">OK</Badge>
                      ) : (
                        <Badge tone="flagged">Review</Badge>
                      )}
                      <span className="sr-only">
                        {v.reconciled ? "Reconciled" : v.flag_reason ?? "Needs review"}
                      </span>
                    </td>
                  </tr>
                  {showReason && (
                    <tr className="border-b border-[var(--tab-border)] bg-amber-50 last:border-0">
                      <td aria-hidden="true" />
                      <td colSpan={6} className="px-3 pb-2.5 text-xs text-[var(--tab-flagged)]">
                        {v.flag_reason}
                      </td>
                    </tr>
                  )}
                </React.Fragment>
              );
            })}
          </tbody>
        </table>
        <datalist id="tab-categories">
          {knownCategories.map((c) => (
            <option key={c} value={c} />
          ))}
        </datalist>
      </div>

      {flaggedCount > 0 && (
        <p className="text-sm text-gray-600">
          Highlighted rows don&apos;t reconcile against the running balance. Correct
          the figures and the flag clears automatically once the row balances —
          we re-check the maths on every edit.
        </p>
      )}
    </div>
  );
}

function Cell({
  row,
  col,
  value,
  onChange,
  align = "left",
  placeholder,
  list,
}: {
  row: number;
  col: EditableField;
  value: string;
  onChange: (row: number, col: EditableField, value: string) => void;
  align?: "left" | "right";
  placeholder?: string;
  list?: string;
}) {
  // Spreadsheet-style keyboard flow: Enter moves to the same column one row down.
  function onKeyDown(e: React.KeyboardEvent<HTMLInputElement>) {
    if (e.key === "Enter") {
      e.preventDefault();
      const next = document.querySelector<HTMLInputElement>(
        `[data-cell="${row + 1}-${col}"]`,
      );
      next?.focus();
      next?.select();
    }
  }
  return (
    <td className="px-2 py-1 align-middle">
      <input
        value={value}
        placeholder={placeholder}
        list={list}
        data-cell={`${row}-${col}`}
        aria-label={`${col.replace("_", " ")}, row ${row + 1}`}
        onChange={(e) => onChange(row, col, e.target.value)}
        onKeyDown={onKeyDown}
        className={`w-full rounded-[6px] border border-transparent bg-transparent px-2 py-1.5 placeholder:text-gray-400 hover:border-[var(--tab-border)] focus:border-[var(--tab-brand)] focus:bg-white focus:outline-none ${
          align === "right" ? "text-right font-[var(--tab-mono)] tabular-nums" : ""
        }`}
      />
    </td>
  );
}
