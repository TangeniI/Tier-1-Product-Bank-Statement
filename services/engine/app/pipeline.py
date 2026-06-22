"""End-to-end extraction pipeline: bytes → ExtractionResult.

Ingest & classify → match a bank profile → parse layout → normalise → reconcile.
The LLM-assisted fallback referenced in the brief plugs in at the parse step in
a later increment; whatever produces rows, reconciliation is always the final
arbiter of accuracy.
"""
from __future__ import annotations

from .ingest import ingest_pdf
from .parser import parse_document
from .profile_loader import match_profile
from .reconcile import reconcile
from .schema import ExtractionResult, ReconcileSummary


def extract(data: bytes) -> ExtractionResult:
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
    raw_rows, warnings = parse_document(doc, profile)
    rows, summary, confidence = reconcile(raw_rows)

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
