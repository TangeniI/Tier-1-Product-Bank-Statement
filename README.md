# Tabular

Turn a bank/credit-card statement PDF into a clean, accurate **CSV or Excel** file — with every transaction **verified against the statement's own running balance**, so bookkeepers and small businesses stop re-typing statements by hand.

> Working name was "LedgerLift"; the product is **Tabular** (`@tabular/*`). UK-focused, accuracy + privacy first.

## What's here (Increment 1 — vertical slice)
A demoable end-to-end slice for **one bank** (Barclays-style, text-layer PDFs):
upload → layout-aware extraction → **balance reconciliation + confidence + row flagging** → first-pass categorisation → inline edit (with live re-reconciliation) → export CSV/XLSX/**OFX·QBO** with accounting presets (Xero / QuickBooks / FreeAgent).

Notable engine capabilities:
- **Yearless dates** ("02 Apr") are resolved from the statement period, including the Dec→Jan year boundary.
- **Keyword categorisation** (`categories.yaml`, data not code) gives every row a first-pass nominal category the user can correct.
- **Duplicate detection** flags repeated (date, amount, description) rows.
- **Live re-reconciliation**: the web UI re-checks the running balance on every edit (`apps/tabular/lib/reconcile.ts` mirrors the engine), so the trust signals never go stale.
- **Accuracy harness** (`services/engine/scripts/eval.py`) prints a per-statement reconciliation scorecard; CI runs tests + the scorecard + the web build.

Deferred to later increments: live Supabase auth, live Stripe billing, OCR/scanned PDFs (the natural home for an LLM extractor verified by reconciliation), more banks, SEO/programmatic pages, deployment. Those packages (`auth`, `billing`, `analytics`) are built here as typed skeletons.

## Monorepo layout
```
packages/
  ui          shared React + Tailwind components + design tokens
  auth        Supabase wrapper        — skeleton (typed interface + env)
  billing     Stripe + pricing config — skeleton
  analytics   PostHog/Plausible       — skeleton (no-op tracker)
apps/
  tabular     Next.js web app  (@tabular/web)
services/
  engine      Python FastAPI extraction service (the moat)
```

## Prerequisites
- Node ≥ 20 + pnpm (`corepack enable && corepack prepare pnpm@9.15.0 --activate`)
- Python 3.12

## Setup
```bash
# 1. JS workspace
pnpm install

# 2. Python engine
cd services/engine && python3 -m venv .venv && .venv/bin/pip install -r requirements-dev.txt && cd ../..

# 3. Env
cp .env.example apps/tabular/.env.local   # ENGINE_URL defaults to localhost:8000
```

## Run everything
```bash
pnpm dev:all      # engine (:8000) + web (:3000) together
```
Or separately:
```bash
# engine
cd services/engine && .venv/bin/python -m uvicorn app.main:app --reload --port 8000
# web
pnpm --filter @tabular/web dev
```
Open http://localhost:3000 and upload a statement. To generate a sample PDF:
```bash
cd services/engine && .venv/bin/python scripts/make_fixture.py /tmp/barclays_sample.pdf
```

## Test
```bash
cd services/engine && .venv/bin/python -m pytest   # engine + reconciliation + export
pnpm --filter @tabular/web build                   # web typecheck + build
```

## Trust & privacy
- **Verified against your statement's running balance** — the accuracy guarantee.
- **We never store your statements or train on your data** — processed in memory, deleted after conversion.
