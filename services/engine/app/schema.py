"""API + internal data models for the extraction engine.

Money on the API boundary is expressed in pounds (float, 2dp) because that is
what the UI table and accounting exports expect. Internally the pipeline works
in integer **pence** to keep reconciliation arithmetic exact — see
`normalize.py` and `reconcile.py`.
"""
from __future__ import annotations

from typing import Literal, Optional

from pydantic import BaseModel, Field


class Transaction(BaseModel):
    """One statement line on the API boundary."""

    date: str = Field(description="ISO date (YYYY-MM-DD) when parseable, else raw text")
    description: str = ""
    money_in: Optional[float] = None
    money_out: Optional[float] = None
    balance: Optional[float] = None
    category: Optional[str] = None
    reconciled: bool = True
    flag_reason: Optional[str] = None


class ReconcileSummary(BaseModel):
    total_rows: int = 0
    movement_rows: int = 0
    reconciled_rows: int = 0
    flagged_rows: int = 0
    opening_balance: Optional[float] = None
    closing_balance: Optional[float] = None
    computed_closing: Optional[float] = None
    balanced: bool = False


class ExtractionResult(BaseModel):
    bank_profile: str
    page_count: int
    has_text_layer: bool
    overall_confidence: float = Field(ge=0.0, le=1.0)
    rows: list[Transaction] = []
    summary: ReconcileSummary = ReconcileSummary()
    warnings: list[str] = []


class ExportRequest(BaseModel):
    rows: list[Transaction]
    format: Literal["csv", "xlsx", "ofx"] = "csv"
    preset: str = "default"
    filename: str = "statement"
