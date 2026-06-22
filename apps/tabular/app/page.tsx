"use client";

import * as React from "react";
import { Dropzone } from "@tabular/ui";
import { track } from "@tabular/analytics";
import { ResultsTable } from "@/components/ResultsTable";
import type { ExtractionResult } from "@/lib/types";

type Status = "idle" | "working" | "done" | "error";

export default function Home() {
  const [status, setStatus] = React.useState<Status>("idle");
  const [result, setResult] = React.useState<ExtractionResult | null>(null);
  const [error, setError] = React.useState<string | null>(null);
  const [fileName, setFileName] = React.useState<string>("");

  async function handleFile(file: File) {
    setStatus("working");
    setError(null);
    setFileName(file.name);
    track({ name: "demo_upload_started", props: {} });

    const form = new FormData();
    form.append("file", file);
    try {
      const res = await fetch("/api/extract", { method: "POST", body: form });
      const data = await res.json();
      if (!res.ok) {
        setError(data.detail ?? "Something went wrong.");
        setStatus("error");
        return;
      }
      const r = data as ExtractionResult;
      setResult(r);
      setStatus("done");
      track({
        name: "extraction_completed",
        props: {
          bankProfile: r.bank_profile,
          confidence: r.overall_confidence,
          flaggedRows: r.summary.flagged_rows,
        },
      });
    } catch {
      setError("Could not reach the server. Please try again.");
      setStatus("error");
    }
  }

  function reset() {
    setStatus("idle");
    setResult(null);
    setError(null);
  }

  return (
    <main className="mx-auto max-w-5xl px-5 py-10">
      <header className="mb-8 flex items-center justify-between">
        <div className="text-xl font-bold tracking-tight">
          Tabular
          <span className="ml-2 align-middle text-xs font-normal text-gray-500">
            beta
          </span>
        </div>
        <nav className="text-sm text-gray-600">UK bank statements → CSV / Excel</nav>
      </header>

      {status !== "done" && (
        <section className="mb-8 text-center">
          <h1 className="mx-auto max-w-2xl text-3xl font-bold leading-tight sm:text-4xl">
            Convert a bank statement PDF to clean CSV or Excel
          </h1>
          <p className="mx-auto mt-3 max-w-xl text-gray-600">
            Every row is verified against your statement&apos;s own running
            balance, so the numbers are right. We never store your statements or
            train on your data.
          </p>
        </section>
      )}

      {(status === "idle" || status === "error") && (
        <section className="mx-auto max-w-2xl">
          <Dropzone onFile={handleFile} />
          {error && (
            <p className="mt-3 rounded-[8px] bg-red-50 p-3 text-sm text-[var(--tab-error)]">
              {error}
            </p>
          )}
          <ul className="mt-6 flex flex-wrap justify-center gap-x-6 gap-y-2 text-sm text-gray-500">
            <li>✓ Balance-reconciled accuracy</li>
            <li>✓ Xero / QuickBooks / FreeAgent presets</li>
            <li>✓ Deleted after processing</li>
          </ul>
          <p className="mt-4 text-center text-xs text-gray-400">
            Supports Barclays today · more UK banks coming. First statement free.
          </p>
        </section>
      )}

      {status === "working" && (
        <section className="mx-auto max-w-md py-16 text-center">
          <div className="mx-auto mb-4 h-8 w-8 animate-spin rounded-full border-2 border-[var(--tab-border)] border-t-[var(--tab-brand)]" />
          <p className="text-gray-600">
            Reading {fileName || "your statement"} and reconciling the balance…
          </p>
        </section>
      )}

      {status === "done" && result && (
        <section>
          <div className="mb-5 flex items-center justify-between">
            <h2 className="text-lg font-semibold">{fileName || "Your statement"}</h2>
            <button
              onClick={reset}
              className="text-sm text-[var(--tab-brand-dark)] underline"
            >
              Convert another
            </button>
          </div>
          <ResultsTable result={result} />
        </section>
      )}

      <footer className="mt-16 border-t border-[var(--tab-border)] pt-6 text-center text-xs text-gray-400">
        Tabular · Statements processed in memory and deleted after conversion ·
        We don&apos;t train on your data.
      </footer>
    </main>
  );
}
