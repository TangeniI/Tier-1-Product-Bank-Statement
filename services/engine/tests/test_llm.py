"""Scanned-PDF / LLM extraction path. Uses a fake extractor so no API key or
network is needed — the point under test is that the LLM's output is verified by
the same reconciliation as everything else ("LLM proposes, math disposes")."""
from app.ingest import IngestedDoc
from app.llm_extractor import get_extractor
from app.pipeline import extract


class FakeExtractor:
    def __init__(self, payload: dict):
        self.payload = payload

    def extract(self, pdf_bytes: bytes) -> dict:
        return self.payload


def _scanned_doc() -> IngestedDoc:
    # No text layer → routes to the scanned/LLM branch.
    return IngestedDoc(page_count=1, has_text_layer=False, pages=[], full_text="")


CLEAN = {
    "opening_balance": 1000.0,
    "transactions": [
        {"date": "02 Apr 2026", "description": "TESCO STORES", "money_out": 45.50, "balance": 954.50},
        {"date": "05 Apr 2026", "description": "Salary ACME LTD", "money_in": 2000.0, "balance": 2954.50},
    ],
}


def test_llm_path_reconciles_and_categorises():
    r = extract(b"scanned-bytes", doc=_scanned_doc(), llm=FakeExtractor(CLEAN))
    assert r.bank_profile == "scanned (AI vision)"
    assert r.has_text_layer is False
    assert len(r.rows) == 2
    assert r.summary.flagged_rows == 0
    assert r.summary.balanced is True
    assert r.rows[0].category == "Groceries & Supplies"


def test_llm_hallucinated_balance_is_flagged():
    bad = {
        "opening_balance": 1000.0,
        "transactions": [
            {"date": "02 Apr 2026", "description": "TESCO", "money_out": 45.50, "balance": 954.50},
            # Model misreads the balance — reconciliation must catch it.
            {"date": "05 Apr 2026", "description": "Salary", "money_in": 2000.0, "balance": 9999.99},
        ],
    }
    r = extract(b"x", doc=_scanned_doc(), llm=FakeExtractor(bad))
    assert r.summary.flagged_rows == 1
    flagged = [t for t in r.rows if not t.reconciled]
    assert flagged[0].description == "Salary"


def test_no_extractor_returns_clear_message():
    r = extract(b"x", doc=_scanned_doc(), llm=None)
    assert r.rows == []
    assert any("scanned" in w.lower() for w in r.warnings)


def test_get_extractor_disabled_without_key(monkeypatch):
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    assert get_extractor() is None
