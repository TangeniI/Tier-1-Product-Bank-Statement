# Tabular

Turn a bank or credit-card statement PDF into a clean **CSV / Excel / OFX** file — with **every transaction verified against the statement's own running balance**, so anything that doesn't add up is flagged instead of silently trusted.

**▶ Live demo: https://tier-1-product-bank-statement-tabul.vercel.app**
*(The extraction engine runs on a free tier and is kept warm by a cron ping; if it's been idle the first request may take a few seconds.)*

> **What makes it different.** The market splits into *template-based* converters (accurate only on banks they have a template for) and *AI-based* ones (flexible but unverifiable). Tabular does both — a deterministic parser for text-layer PDFs, a vision LLM for scanned ones — and runs **both** through the same running-balance reconciliation. **The maths is the single arbiter of accuracy: "the LLM proposes, the maths disposes."**

---

## How it works

```
        upload PDF
            │
   ┌────────┴─────────┐
   │  text layer?     │
   └────────┬─────────┘
       yes  │  no
   ┌────────┘     └──────────┐
   ▼                         ▼
deterministic            vision LLM (Gemini)
layout parser            structured extraction
   │                         │
   └───────────┬─────────────┘
               ▼
   running-balance RECONCILIATION   ← integer-pence, exact; the trust layer
   (flag every row that doesn't tie out + confidence score)
               ▼
   categorise · detect duplicates · inline edit (live re-reconcile)
               ▼
   export CSV / Excel / OFX·QBO   (Xero · QuickBooks · FreeAgent · UK VAT presets)
```

Whatever produces the rows, reconciliation is always the final step — so a hallucinated or mis-parsed figure surfaces as a flagged, non-reconciling row rather than a silent error.

## Engineering highlights

- **Reconciliation as the accuracy guarantee** — `previous_balance + money_in − money_out == stated_balance`, in **integer pence** so the arithmetic is exact. Non-reconciling rows are flagged, never auto-"fixed".
- **Hybrid extraction** — deterministic positional parser (zero marginal cost) for text PDFs; **Google Gemini** vision for scanned PDFs, provider-agnostic behind a small interface and verified by the same reconciliation.
- **Profiles-as-data** — adding a bank is a YAML file, not code. Two layouts shipped: Barclays (split money in/out columns) and Starling (single signed-amount column). Yearless dates ("02 Apr") are resolved from the statement period, including the Dec→Jan boundary.
- **Live re-reconciliation** — the web UI re-checks the whole balance chain on every cell edit (`apps/tabular/lib/reconcile.ts` mirrors the Python engine), so the trust signals never go stale.
- **Privacy by construction** — statements are processed in memory and never written to disk; this is enforced by a test (`tests/test_privacy.py`), not just promised.
- **Tested & measured** — 38 engine tests, plus an accuracy harness (`scripts/eval.py`) that prints a per-statement reconciliation scorecard. CI runs tests + the scorecard + the web build on every push.
- **Shipped & hardened** — deployed (Vercel + Render), patched a real critical CVE (React2Shell / CVE-2025-55182) under deploy pressure, and locked the engine behind a shared-secret token + origin CORS.

## Tech stack

| Layer | Stack |
|-------|-------|
| Web | Next.js 15 (App Router) · React 19 · TypeScript (strict) · Tailwind |
| Engine | Python 3.12 · FastAPI · pdfplumber · pandas · Pydantic |
| AI | Google Gemini (vision, structured JSON output) for scanned PDFs |
| Tooling | pnpm + Turborepo monorepo · pytest · GitHub Actions CI |
| Deploy | Vercel (web) · Render / Docker (engine) |

## Project layout

```
packages/
  ui          shared React + Tailwind components + design tokens
  auth        Supabase wrapper        — typed skeleton (post-launch)
  billing     Stripe + pricing config — typed skeleton (post-launch)
  analytics   PostHog/Plausible       — no-op tracker skeleton
apps/
  tabular     Next.js web app (@tabular/web)
services/
  engine      Python FastAPI extraction service — the core
```

## Run it locally

**Prerequisites:** Node ≥ 20 + pnpm (`corepack enable && corepack prepare pnpm@9.15.0 --activate`), Python 3.12.

```bash
# 1. JS workspace
pnpm install

# 2. Python engine
cd services/engine && python3 -m venv .venv && .venv/bin/pip install -r requirements-dev.txt && cd ../..

# 3. Env
cp .env.example apps/tabular/.env.local   # ENGINE_URL defaults to localhost:8000

# 4. Run engine (:8000) + web (:3000) together
pnpm dev:all
```

Open http://localhost:3000 and upload a statement. Generate a sample to try:

```bash
cd services/engine && .venv/bin/python scripts/make_fixture.py /tmp/barclays_sample.pdf
```

Scanned-PDF (AI) extraction activates when `GEMINI_API_KEY` is set on the engine; without it, text-layer PDFs work exactly as above.

## Test

```bash
cd services/engine && .venv/bin/python -m pytest    # 38 tests: parser, reconciliation, export, LLM path, privacy
cd services/engine && .venv/bin/python scripts/eval.py   # accuracy scorecard
pnpm --filter @tabular/web typecheck                 # strict TS
pnpm --filter @tabular/web build                     # production build
```

## What I'd build next

- Direct push into Xero/QuickBooks via their APIs (not just file export) — the market's top convenience feature.
- A growing corpus of real (anonymised) statements per bank, tracked by the eval harness.
- Wire the auth/billing skeletons for paid plans.

---

*Tabular is a solo portfolio project built to demonstrate full-stack and applied-AI engineering — from a layout-aware PDF parser and exact financial reconciliation to an LLM extraction path, a tested monorepo, CI, and a live two-service deployment. UK-focused, accuracy- and privacy-first.*
