# Tabular Engine

FastAPI service that turns a bank-statement PDF into normalised, **balance-reconciled** rows and exports CSV/XLSX.

## Pipeline
`ingest` (text-layer vs scanned) → `profile_loader` (auto-match a YAML bank profile) → `parser` (layout-aware, positional columns + multi-line descriptions) → `normalize` (robust date/amount parsing, integer pence) → `reconcile` (row-by-row running-balance check + confidence) → `export` (CSV/XLSX + accounting presets).

Every figure must reconcile against the statement's own running balance or it is **flagged** — never silently "fixed".

## Run locally
```bash
cd services/engine
python3 -m venv .venv
.venv/bin/pip install -r requirements-dev.txt
.venv/bin/python -m uvicorn app.main:app --reload --port 8000
```

## Endpoints
- `GET  /healthz` — liveness
- `GET  /presets` — export presets for the UI
- `POST /extract` — multipart PDF → `ExtractionResult`
- `POST /export` — rows + `{format, preset}` → CSV/XLSX download

## Tests & fixtures
```bash
.venv/bin/python -m pytest
# regenerate the synthetic sample PDF:
.venv/bin/python scripts/make_fixture.py barclays_sample.pdf
```
The test fixture is a synthetic Barclays-style statement (`scripts/make_fixture.py`) including a multi-line description and one deliberately non-reconciling row, so the flagging path is always covered. Swap in real redacted statements here to harden profiles.

## Adding a bank
Add a YAML file under `app/profiles/` (see `barclays.yaml`). Adding a bank = adding config, not code. The `generic.yaml` fallback handles unmatched layouts at lower confidence.

## Privacy
Uploads are processed entirely in memory — no statement bytes are written to disk.
