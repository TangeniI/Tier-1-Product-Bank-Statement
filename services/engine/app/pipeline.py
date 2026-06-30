"""End-to-end extraction pipeline: bytes → ExtractionResult.

Ingest & classify → match a bank profile → parse layout → normalise → reconcile.
Whatever produces rows — the deterministic positional parser for text-layer PDFs,
or the vision LLM for scanned ones (see llm_extractor) — reconciliation is always
the final arbiter of accuracy.
"""
from __future__ import annotations

import logging
from typing import Optional

from .categorize import categorize
from .ingest import IngestedDoc, ingest_pdf
from .llm_extractor import LLMExtractor, get_extractor
from .normalize import dominant_year, extract_statement_period, parse_date, pounds_to_pence
from .parser import RawRow, parse_document
from .profile_loader import get_generic_profile, match_profile
from .reconcile import reconcile
from .schema import ExtractionResult, ReconcileSummary, Transaction

logger = logging.getLogger("tabular.pipeline")


def extract(
    data: bytes,
    doc: IngestedDoc | None = None,
    llm: Optional[LLMExtractor] = None,
) -> ExtractionResult:
    # Callers that already ingested the PDF (e.g. the API's page-count guard)
    # pass `doc` through so the expensive pdfplumber parse runs only once.
    if doc is None:
        doc = ingest_pdf(data)

    if not doc.has_text_layer:
        return _extract_scanned(data, doc, llm)

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


def _extract_scanned(
    data: bytes, doc: IngestedDoc, llm: Optional[LLMExtractor]
) -> ExtractionResult:
    """Scanned PDF (no text layer). If a vision LLM is configured, let it read
    the document, then verify its output through the same reconciliation."""
    extractor = llm or get_extractor()
    if extractor is None:
        return ExtractionResult(
            bank_profile="unknown",
            page_count=doc.page_count,
            has_text_layer=False,
            overall_confidence=0.0,
            rows=[],
            summary=ReconcileSummary(),
            warnings=[
                "This looks like a scanned PDF (no text layer). AI extraction is "
                "available but not enabled on this instance — for now please upload "
                "a text-based statement."
            ],
        )

    try:
        payload = extractor.extract(data)
    except Exception as exc:
        # Log the failure (exception only — never statement content) so prod
        # errors are diagnosable.
        logger.warning("LLM extraction failed: %s: %s", type(exc).__name__, exc)
        return ExtractionResult(
            bank_profile="scanned",
            page_count=doc.page_count,
            has_text_layer=False,
            overall_confidence=0.0,
            rows=[],
            summary=ReconcileSummary(),
            warnings=["AI extraction failed to read this scanned PDF. Please try again."],
        )

    raw_rows = _raw_rows_from_llm(payload)
    rows, summary, confidence = reconcile(raw_rows)
    for row in rows:
        row.category = categorize(row.description)

    warnings = [
        "Extracted from a scanned PDF using AI vision. Every row was still checked "
        "against the running balance — review any flagged rows carefully."
    ]
    if not rows:
        warnings.append("No transactions could be read from this statement.")

    return ExtractionResult(
        bank_profile="scanned (AI vision)",
        page_count=doc.page_count,
        has_text_layer=False,
        overall_confidence=confidence,
        rows=rows,
        summary=summary,
        warnings=warnings,
    )


def _raw_rows_from_llm(payload: dict) -> list[RawRow]:
    """Convert the LLM's JSON into the same RawRow shape the parser produces, so
    it flows through reconciliation unchanged."""
    txns = payload.get("transactions") or []
    fmts = get_generic_profile().date_formats
    # Resolve yearless dates from any year the model did print.
    default_year = dominant_year(" ".join(str(t.get("date", "")) for t in txns))

    rows: list[RawRow] = []
    opening = payload.get("opening_balance")
    if opening is not None:
        rows.append(RawRow(None, "", "", None, None, pounds_to_pence(opening), "opening"))
    for t in txns:
        raw = str(t.get("date", "")).strip()
        rows.append(
            RawRow(
                date_iso=parse_date(raw, fmts, default_year=default_year),
                date_raw=raw,
                description=str(t.get("description", "")),
                money_out=pounds_to_pence(t.get("money_out")),
                money_in=pounds_to_pence(t.get("money_in")),
                balance=pounds_to_pence(t.get("balance")),
                kind="txn",
            )
        )
    return rows


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
