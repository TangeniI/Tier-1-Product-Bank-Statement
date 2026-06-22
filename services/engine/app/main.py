"""FastAPI surface for the Tabular extraction engine.

Endpoints:
  GET  /healthz   — liveness
  GET  /presets   — available export presets (for the UI dropdown)
  POST /extract   — multipart PDF → ExtractionResult
  POST /export    — (possibly edited) rows → CSV/XLSX download

Privacy: uploads are processed entirely in memory and never written to disk.
"""
from __future__ import annotations

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse

from .config import ALLOWED_ORIGINS, MAX_EXPORT_ROWS, MAX_PAGES
from .export import list_presets, to_csv, to_ofx, to_xlsx
from .ingest import ingest_pdf
from .pipeline import extract
from .schema import ExportRequest, ExtractionResult

app = FastAPI(title="Tabular Engine", version="0.1.0")

# The Next.js app calls the engine server-side. CORS defaults to permissive for
# local dev; set ENGINE_ALLOWED_ORIGINS to the app origin(s) in production.
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/healthz")
def healthz() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/presets")
def presets() -> list[dict[str, str]]:
    return list_presets()


@app.post("/extract", response_model=ExtractionResult)
async def extract_endpoint(file: UploadFile = File(...)) -> ExtractionResult:
    if file.content_type not in ("application/pdf", "application/octet-stream", None):
        raise HTTPException(status_code=415, detail="Please upload a PDF file.")
    data = await file.read()
    if not data:
        raise HTTPException(status_code=400, detail="Empty file.")

    # Page-count guard before the heavier parse.
    try:
        doc = ingest_pdf(data)
    except Exception:
        raise HTTPException(status_code=422, detail="Could not read this PDF.")
    if doc.page_count > MAX_PAGES:
        raise HTTPException(
            status_code=413,
            detail=f"Statement has {doc.page_count} pages; the limit is {MAX_PAGES}.",
        )

    # Reuse the doc we just parsed for the guard — don't re-ingest.
    return extract(data, doc=doc)


@app.post("/export")
def export_endpoint(req: ExportRequest) -> StreamingResponse:
    if len(req.rows) > MAX_EXPORT_ROWS:
        raise HTTPException(
            status_code=413,
            detail=f"Too many rows ({len(req.rows)}); the limit is {MAX_EXPORT_ROWS}.",
        )
    if req.format == "csv":
        payload = to_csv(req.rows, req.preset)
        media = "text/csv"
        ext = "csv"
    elif req.format == "ofx":
        payload = to_ofx(req.rows, req.preset)
        media = "application/x-ofx"
        ext = "ofx"
    else:
        payload = to_xlsx(req.rows, req.preset)
        media = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        ext = "xlsx"

    import io

    filename = f"{req.filename}-{req.preset}.{ext}"
    return StreamingResponse(
        io.BytesIO(payload),
        media_type=media,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
