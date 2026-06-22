"""Ingest & classify: open a PDF from bytes and decide text-layer vs scanned.

Everything operates on an in-memory buffer — no statement bytes are written to
disk (the privacy stance). The caller is responsible for not persisting input.
"""
from __future__ import annotations

import io
from dataclasses import dataclass, field

import pdfplumber

from .config import MIN_CHARS_PER_PAGE_FOR_TEXT_LAYER


@dataclass
class IngestedPage:
    index: int
    text: str
    words: list[dict] = field(default_factory=list)


@dataclass
class IngestedDoc:
    page_count: int
    has_text_layer: bool
    pages: list[IngestedPage]
    full_text: str


def ingest_pdf(data: bytes) -> IngestedDoc:
    """Parse a PDF held in memory into pages with text + positioned words."""
    pages: list[IngestedPage] = []
    with pdfplumber.open(io.BytesIO(data)) as pdf:
        for i, page in enumerate(pdf.pages):
            text = page.extract_text() or ""
            words = page.extract_words(
                use_text_flow=False, keep_blank_chars=False, extra_attrs=["size"]
            )
            pages.append(IngestedPage(index=i, text=text, words=words))

    page_count = len(pages)
    total_chars = sum(len(p.text) for p in pages)
    avg_chars = total_chars / page_count if page_count else 0
    has_text_layer = avg_chars >= MIN_CHARS_PER_PAGE_FOR_TEXT_LAYER
    full_text = "\n".join(p.text for p in pages)

    return IngestedDoc(
        page_count=page_count,
        has_text_layer=has_text_layer,
        pages=pages,
        full_text=full_text,
    )
