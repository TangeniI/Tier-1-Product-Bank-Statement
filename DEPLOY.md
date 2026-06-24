# Deploying Tabular

Tabular is two services:

- **Web** (`apps/tabular`) — Next.js → **Vercel**
- **Engine** (`services/engine`) — Python/FastAPI → **Render** (or Railway/Fly)

Deploy the engine first, then point the web app at it.

---

## 1. Engine → Render

The repo includes [`render.yaml`](render.yaml) and [`services/engine/Dockerfile`](services/engine/Dockerfile).

1. Push this repo to GitHub.
2. In Render: **New → Blueprint**, select the repo. Render reads `render.yaml` and creates the `tabular-engine` web service from the Dockerfile.
3. Set env vars on the service:
   - `ENGINE_ALLOWED_ORIGINS` → your Vercel URL (e.g. `https://tabular.vercel.app`). Leave as `*` only while testing.
   - `GEMINI_API_KEY` → *(optional)* enables AI extraction of scanned PDFs. Get one at <https://aistudio.google.com/apikey>.
4. Deploy. Confirm `https://<your-engine>.onrender.com/healthz` returns `{"status":"ok"}`.

> **Railway/Fly alternative:** point the platform at `services/engine/Dockerfile` and set the same env vars. Any host that runs a Docker container works.

---

## 2. Web → Vercel

The app is a pnpm-workspace package, so set the build to run from the repo root.

1. In Vercel: **Add New → Project**, import the repo.
2. Settings:
   - **Root Directory:** `apps/tabular`
   - **Framework Preset:** Next.js (auto-detected)
   - Vercel detects pnpm and installs the workspace automatically.
3. Environment variable:
   - `ENGINE_URL` → your Render engine URL (e.g. `https://tabular-engine.onrender.com`). This stays server-side; it's never exposed to the browser.
4. Deploy.

---

## 3. Lock it down

- Set `ENGINE_ALLOWED_ORIGINS` on the engine to the exact Vercel origin (not `*`).
- Re-deploy the engine so CORS takes effect.
- Smoke-test: open the Vercel URL, upload `barclays_sample.pdf` (generate with
  `python services/engine/scripts/make_fixture.py /tmp/barclays_sample.pdf`),
  confirm extraction, reconciliation, and a CSV/OFX export.

## Notes

- **Free-tier engines sleep.** Render's free plan cold-starts after inactivity;
  the first upload may take a few seconds. Fine for a portfolio demo.
- **Privacy holds in prod:** the engine processes statements in memory and never
  writes them to disk (enforced by `tests/test_privacy.py`).
- **No billing in v1:** auth/billing are typed skeletons; the live demo is free
  and anonymous.
