"""End-to-end extraction pipeline: bytes → ExtractionResult.

Ingest & classify → match a bank profile → parse layout → normalise → reconcile.
The LLM-assisted fallback referenced in the brief plugs in at the parse step in
a later increment; whatever produces rows, reconciliation is always the final
arbiter of accuracy.
"""
from __future__ import annotations

from .categorize import categorize
from .ingest import IngestedDoc, ingest_pdf
from .normalize import dominant_year, extract_statement_period
from .parser import parse_document
from .profile_loader import match_profile
from .reconcile import reconcile
from .schema import ExtractionResult, ReconcileSummary, Transaction


def extract(data: bytes, doc: IngestedDoc | None = None) -> ExtractionResult:
    # Callers that already ingested the PDF (e.g. the API's page-count guard)
    # pass `doc` through so the expensive pdfplumber parse runs only once.
    if doc is None:
        doc = ingest_pdf(data)

    if not doc.has_text_layer:
        # Scanned PDF — OCR path is a later increment. Fail clearly, don't guess.
        return ExtractionResult(
            bank_profile="unknown",
            page_count=doc.page_count,
            has_text_layer=False,
            overall_confidence=0.0,
            rows=[],
            summary=ReconcileSummary(),
            warnings=[
                "This looks like a scanned PDF (no text layer). OCR support is "
                "coming soon; for now please upload a text-based statement."
            ],
        )

    profile = match_profile(doc.full_text)

    # Resolve the year for statements that print yearless dates ("02 Apr"):
    # prefer the explicit statement period, fall back to the dominant year.
    period = extract_statement_period(doc.full_text)
    default_year = None if period else dominant_year(doc.full_text)

    raw_rows, warnings = parse_document(doc, profile, period, default_year)
    rows, summary, confidence = reconcile(raw_rows)

    # First-pass categorisation (user can correct inline) + a duplicate heads-up.
    for row in rows:
        row.category = categorize(row.description)
    dupes = _count_duplicates(rows)
    if dupes:
        warnings.append(
            f"{dupes} possible duplicate {'transaction' if dupes == 1 else 'transactions'} "
            "detected (same date, amount and description) — please review."
        )

    if not rows:
        warnings.append("No transactions could be extracted from this statement.")

    return ExtractionResult(
        bank_profile=profile.name,
        page_count=doc.page_count,
        has_text_layer=True,
        overall_confidence=confidence,
        rows=rows,
        summary=summary,
        warnings=warnings,
    )


def _count_duplicates(rows: list[Transaction]) -> int:
    """Count rows beyond the first occurrence of each (date, in, out, desc)."""
    seen: set[tuple] = set()
    dupes = 0
    for r in rows:
        key = (r.date, r.money_in, r.money_out, r.description.strip().lower())
        if key in seen:
            dupes += 1
        else:
            seen.add(key)
    return dupes
