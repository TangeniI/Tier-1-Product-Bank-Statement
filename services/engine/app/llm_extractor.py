"""LLM-assisted extraction for scanned / image-only PDFs.

The deterministic parser only works on PDFs with a real text layer. Scanned
statements have no text to position, so here a vision LLM reads the document and
proposes transactions — but it is NOT trusted blindly: the rows it returns flow
through the exact same `reconcile()` step as everything else. The running-balance
maths remains the single arbiter of accuracy, so a hallucinated figure shows up
as a flagged, non-reconciling row rather than a silent error.

    "LLM proposes, math disposes."

Provider-agnostic by design: `LLMExtractor` is a tiny protocol, and `GeminiExtractor`
is the default implementation (Google Gemini — native PDF understanding, JSON
schema output). Swapping in Claude or another provider is a new class, nothing
else changes. The feature is inert unless GEMINI_API_KEY is set, so local dev and
CI run exactly as before.
"""
from __future__ import annotations

import base64
import json
import os
import ssl
import time
import urllib.error
import urllib.request
from typing import Optional, Protocol

# Transient HTTP statuses worth retrying, and backoff config.
_RETRY_STATUS = {429, 500, 502, 503}
_MAX_RETRIES = 3
_BACKOFF_BASE = 1.5  # seconds: 1.5, 3.0, ...


def _ssl_context() -> ssl.SSLContext:
    """Verified TLS context. Prefer certifi's CA bundle when present so the call
    works on machines whose Python lacks system CA certs (common on macOS)."""
    try:
        import certifi

        return ssl.create_default_context(cafile=certifi.where())
    except Exception:
        return ssl.create_default_context()

# Default model — fast + cheap, strong document understanding. Override with
# LLM_MODEL. Provider/key via GEMINI_API_KEY.
DEFAULT_MODEL = os.environ.get("LLM_MODEL", "gemini-2.5-flash")
_GEMINI_ENDPOINT = (
    "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
)

_PROMPT = (
    "You are extracting transactions from a bank or credit-card statement. "
    "Return every transaction line in order. For each, give the date exactly as "
    "printed, the description, and the amounts in pounds as numbers. Use money_in "
    "for credits/paid-in and money_out for debits/paid-out (positive numbers; "
    "leave the other null). Include the running balance if shown. Also return the "
    "opening balance if the statement states one. Do not invent or correct figures "
    "— transcribe exactly what is printed."
)

# Gemini structured-output schema (OpenAPI subset).
_SCHEMA = {
    "type": "OBJECT",
    "properties": {
        "opening_balance": {"type": "NUMBER", "nullable": True},
        "transactions": {
            "type": "ARRAY",
            "items": {
                "type": "OBJECT",
                "properties": {
                    "date": {"type": "STRING"},
                    "description": {"type": "STRING"},
                    "money_in": {"type": "NUMBER", "nullable": True},
                    "money_out": {"type": "NUMBER", "nullable": True},
                    "balance": {"type": "NUMBER", "nullable": True},
                },
                "required": ["date", "description"],
            },
        },
    },
    "required": ["transactions"],
}


class LLMExtractor(Protocol):
    """Returns a dict: {opening_balance: float|None, transactions: [ {date,
    description, money_in, money_out, balance} ]}."""

    def extract(self, pdf_bytes: bytes) -> dict: ...


class GeminiExtractor:
    def __init__(self, api_key: str, model: str = DEFAULT_MODEL, timeout: int = 60):
        self.api_key = api_key
        self.model = model
        self.timeout = timeout

    def extract(self, pdf_bytes: bytes) -> dict:
        body = {
            "contents": [
                {
                    "parts": [
                        {
                            "inline_data": {
                                "mime_type": "application/pdf",
                                "data": base64.b64encode(pdf_bytes).decode("ascii"),
                            }
                        },
                        {"text": _PROMPT},
                    ]
                }
            ],
            "generationConfig": {
                "responseMimeType": "application/json",
                "responseSchema": _SCHEMA,
            },
        }
        url = _GEMINI_ENDPOINT.format(model=self.model)
        data = json.dumps(body).encode("utf-8")
        ctx = _ssl_context()

        # Retry transient errors (rate limits / model busy) with backoff — Gemini
        # returns 429/503 under load. Other errors fail fast.
        last_exc: Exception | None = None
        for attempt in range(_MAX_RETRIES):
            req = urllib.request.Request(
                url,
                data=data,
                headers={"Content-Type": "application/json", "x-goog-api-key": self.api_key},
                method="POST",
            )
            try:
                with urllib.request.urlopen(req, timeout=self.timeout, context=ctx) as resp:
                    payload = json.loads(resp.read().decode("utf-8"))
                candidates = payload.get("candidates") or []
                if not candidates:
                    # No output (e.g. safety block / empty response) — surface
                    # clearly instead of an IndexError.
                    raise RuntimeError("LLM returned no candidates")
                text = candidates[0]["content"]["parts"][0]["text"]
                return json.loads(text)
            except urllib.error.HTTPError as e:
                last_exc = e
                if e.code in _RETRY_STATUS and attempt < _MAX_RETRIES - 1:
                    time.sleep(_BACKOFF_BASE * (2**attempt))
                    continue
                raise
        raise last_exc if last_exc else RuntimeError("LLM extraction failed")


def get_extractor() -> Optional[LLMExtractor]:
    """The configured extractor, or None when no provider key is set."""
    key = os.environ.get("GEMINI_API_KEY")
    if key:
        return GeminiExtractor(key)
    return None


def llm_available() -> bool:
    return get_extractor() is not None
