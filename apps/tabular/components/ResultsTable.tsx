"use client";

import * as React from "react";
import { Badge, Button, ConfidenceBadge } from "@tabular/ui";
import { track } from "@tabular/analytics";
import type { ExtractionResult, Preset, Transaction } from "@/lib/types";

function money(n: number | null): string {
  return n == null ? "" : n.toFixed(2);
}

function parseMoney(v: string): number | null {
  const t = v.trim();
  if (t === "") return null;
  const n = Number(t.replace(/[£,\s]/g, ""));
  return Number.isFinite(n) ? n : null;
}

type EditableField = "date" | "description" | "money_in" | "money_out" | "balance";

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

  function updateCell(i: number, field: EditableField, value: string) {
    setRows((prev) => {
      const next = [...prev];
      const row = { ...next[i] } as Transaction;
      if (field === "description" || field === "date") {
        row[field] = value;
      } else {
        row[field] = parseMoney(value);
      }
      // A manual edit clears the flag — the user has reviewed this row.
      row.flag_reason = null;
      row.reconciled = true;
      next[i] = row;
      track({ name: "row_edited", props: {} });
      return next;
    });
  }

  async function doExport(format: "csv" | "xlsx") {
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
      a.download = `statement-${preset}.${format}`;
      document.body.appendChild(a);
      a.click();
      a.remove();
      URL.revokeObjectURL(url);
    } finally {
      setBusy(false);
    }
  }

  const flaggedCount = rows.filter((r) => !r.reconciled).length;
  const s = result.summary;

  return (
    <div className="space-y-5">
      {/* Summary / trust bar */}
      <div className="flex flex-wrap items-center gap-3 rounded-[10px] border border-[var(--tab-border)] bg-white p-4">
        <ConfidenceBadge score={result.overall_confidence} />
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
      </div>

      {/* Editable table */}
      <div className="overflow-x-auto rounded-[10px] border border-[var(--tab-border)] bg-white">
        <table className="w-full border-collapse text-sm">
          <thead>
            <tr className="border-b border-[var(--tab-border)] bg-[var(--tab-surface-muted)] text-left">
              <th className="px-3 py-2 font-medium">Date</th>
              <th className="px-3 py-2 font-medium">Description</th>
              <th className="px-3 py-2 text-right font-medium">Money in</th>
              <th className="px-3 py-2 text-right font-medium">Money out</th>
              <th className="px-3 py-2 text-right font-medium">Balance</th>
              <th className="px-3 py-2 font-medium">Status</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((r, i) => (
              <tr
                key={i}
                className={`border-b border-[var(--tab-border)] last:border-0 ${
                  !r.reconciled ? "bg-amber-50" : ""
                }`}
              >
                <Cell value={r.date} onChange={(v) => updateCell(i, "date", v)} />
                <Cell
                  value={r.description}
                  onChange={(v) => updateCell(i, "description", v)}
                  wide
                />
                <Cell
                  value={money(r.money_in)}
                  onChange={(v) => updateCell(i, "money_in", v)}
                  align="right"
                />
                <Cell
                  value={money(r.money_out)}
                  onChange={(v) => updateCell(i, "money_out", v)}
                  align="right"
                />
                <Cell
                  value={money(r.balance)}
                  onChange={(v) => updateCell(i, "balance", v)}
                  align="right"
                />
                <td className="px-3 py-1.5">
                  {r.reconciled ? (
                    <Badge tone="reconciled">OK</Badge>
                  ) : (
                    <span title={r.flag_reason ?? ""}>
                      <Badge tone="flagged">Review</Badge>
                    </span>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {flaggedCount > 0 && (
        <p className="text-sm text-gray-600">
          Highlighted rows didn&apos;t reconcile against the running balance. Edit
          any cell to correct it — the flag clears once you&apos;ve reviewed it.
        </p>
      )}
    </div>
  );
}

function Cell({
  value,
  onChange,
  align = "left",
  wide = false,
}: {
  value: string;
  onChange: (v: string) => void;
  align?: "left" | "right";
  wide?: boolean;
}) {
  return (
    <td className={`px-2 py-1 ${wide ? "min-w-[240px]" : ""}`}>
      <input
        value={value}
        onChange={(e) => onChange(e.target.value)}
        className={`w-full rounded-[6px] border border-transparent bg-transparent px-1.5 py-1 hover:border-[var(--tab-border)] focus:border-[var(--tab-brand)] focus:bg-white focus:outline-none ${
          align === "right" ? "text-right font-[var(--tab-mono)] tabular-nums" : ""
        }`}
      />
    </td>
  );
}
