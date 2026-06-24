"""Layout-aware parser: turn positioned words into raw statement rows.

Real statements are not ruled tables — they are text positioned in columns. So
rather than rely on table borders, we locate the header line, derive an
x-position band for each column from the header labels, then assign every
subsequent word to a column by its horizontal centre. This also gives us
multi-line descriptions for free: a line with no date in the date band is a
continuation of the previous transaction.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

from .ingest import IngestedDoc, IngestedPage
from .normalize import parse_amount, parse_date
from .profile_loader import BankProfile

Y_TOLERANCE = 3.0  # words within this many points vertically are one line


@dataclass
class RawRow:
    date_iso: Optional[str]
    date_raw: str
    description: str
    money_out: Optional[int]  # positive magnitude, pence
    money_in: Optional[int]  # positive magnitude, pence
    balance: Optional[int]  # signed, pence
    kind: str  # "txn" | "opening" | "closing"


@dataclass
class _Word:
    text: str
    x0: float
    x1: float
    top: float

    @property
    def xc(self) -> float:
        return (self.x0 + self.x1) / 2


@dataclass
class _Line:
    top: float
    words: list[_Word] = field(default_factory=list)

    @property
    def text(self) -> str:
        return " ".join(w.text for w in sorted(self.words, key=lambda w: w.x0))


def _group_lines(words: list[dict]) -> list[_Line]:
    ws = sorted(
        (_Word(w["text"], float(w["x0"]), float(w["x1"]), float(w["top"])) for w in words),
        key=lambda w: (w.top, w.x0),
    )
    lines: list[_Line] = []
    for w in ws:
        if lines and abs(w.top - lines[-1].top) <= Y_TOLERANCE:
            lines[-1].words.append(w)
        else:
            lines.append(_Line(top=w.top, words=[w]))
    return lines


def _match_label_center(line: _Line, labels: tuple[str, ...]) -> Optional[float]:
    """Find a contiguous run of words matching any label; return its x-centre."""
    ordered = sorted(line.words, key=lambda w: w.x0)
    lowers = [w.text.lower() for w in ordered]
    for label in labels:
        tokens = label.lower().split()
        n = len(tokens)
        for i in range(len(ordered) - n + 1):
            if lowers[i : i + n] == tokens:
                return (ordered[i].x0 + ordered[i + n - 1].x1) / 2
    return None


def _find_header(lines: list[_Line], profile: BankProfile) -> Optional[dict[str, float]]:
    for line in lines:
        centers: dict[str, float] = {}
        for field_name, labels in profile.columns.items():
            c = _match_label_center(line, labels)
            if c is not None:
                centers[field_name] = c
        # A header qualifies with a date, a balance, and at least one movement
        # column — either the split money in/out pair or a single signed Amount
        # column (the layout many credit-card / challenger-bank statements use).
        has_movement_col = (
            "money_in" in centers or "money_out" in centers or "amount" in centers
        )
        if "date" in centers and "balance" in centers and has_movement_col:
            return centers
    return None


def _make_assigner(centers: dict[str, float]):
    ordered = sorted(centers.items(), key=lambda kv: kv[1])
    bounds = [
        (ordered[i][1] + ordered[i + 1][1]) / 2 for i in range(len(ordered) - 1)
    ]

    def assign(xc: float) -> str:
        for i, b in enumerate(bounds):
            if xc < b:
                return ordered[i][0]
        return ordered[-1][0]

    return assign


def _cells(line: _Line, assign) -> dict[str, str]:
    buckets: dict[str, list[_Word]] = {}
    for w in line.words:
        buckets.setdefault(assign(w.xc), []).append(w)
    return {
        field_name: " ".join(x.text for x in sorted(ws, key=lambda w: w.x0))
        for field_name, ws in buckets.items()
    }


def _contains_any(text: str, markers: tuple[str, ...]) -> bool:
    low = text.lower()
    return any(m.lower() in low for m in markers)


def parse_document(
    doc: IngestedDoc,
    profile: BankProfile,
    period: Optional[tuple[str, str]] = None,
    default_year: Optional[int] = None,
) -> tuple[list[RawRow], list[str]]:
    """Parse every page into raw rows. Header bands carry over to pages that
    repeat the statement body without re-printing the header.

    `period`/`default_year` resolve the year for statements that print yearless
    dates (e.g. "02 Apr") — see normalize.parse_date.
    """
    rows: list[RawRow] = []
    warnings: list[str] = []
    last_centers: Optional[dict[str, float]] = None

    for page in doc.pages:
        page_rows, last_centers = _parse_page(
            page, profile, last_centers, period, default_year
        )
        rows.extend(page_rows)

    if last_centers is None:
        warnings.append(
            "Could not locate a transaction table header; no columns detected."
        )
    return rows, warnings


def _parse_page(
    page: IngestedPage,
    profile: BankProfile,
    carry_centers: Optional[dict[str, float]],
    period: Optional[tuple[str, str]] = None,
    default_year: Optional[int] = None,
) -> tuple[list[RawRow], Optional[dict[str, float]]]:
    lines = _group_lines(page.words)
    centers = _find_header(lines, profile)

    header_top: Optional[float] = None
    if centers is not None:
        # Only consider lines below the header on this page.
        for line in lines:
            if _find_header([line], profile) is not None:
                header_top = line.top
                break
    else:
        centers = carry_centers  # continuation page

    if centers is None:
        return [], None

    assign = _make_assigner(centers)
    rows: list[RawRow] = []

    for line in lines:
        if header_top is not None and line.top <= header_top + Y_TOLERANCE:
            continue
        cells = _cells(line, assign)
        date_cell = cells.get("date", "")
        desc_cell = cells.get("description", "").strip()
        out_pence = parse_amount(cells.get("money_out", ""))
        in_pence = parse_amount(cells.get("money_in", ""))
        # Single signed "Amount" column: split it into the in/out magnitudes the
        # rest of the pipeline expects (positive = money in, negative = money out).
        amount_pence = parse_amount(cells.get("amount", ""))
        if amount_pence is not None and out_pence is None and in_pence is None:
            if amount_pence < 0:
                out_pence = amount_pence
            else:
                in_pence = amount_pence
        bal_pence = parse_amount(cells.get("balance", ""))
        date_iso = parse_date(date_cell, profile.date_formats, period, default_year)
        has_movement = out_pence is not None or in_pence is not None

        # Opening / closing balance anchors (balance only, no movement).
        if bal_pence is not None and not has_movement and not date_iso:
            if _contains_any(line.text, profile.opening_balance_markers):
                rows.append(RawRow(None, "", desc_cell, None, None, bal_pence, "opening"))
                continue
            if _contains_any(line.text, profile.closing_balance_markers):
                rows.append(RawRow(None, "", desc_cell, None, None, bal_pence, "closing"))
                continue

        if date_iso:
            rows.append(
                RawRow(
                    date_iso=date_iso,
                    date_raw=date_cell.strip(),
                    description=desc_cell,
                    money_out=abs(out_pence) if out_pence is not None else None,
                    money_in=abs(in_pence) if in_pence is not None else None,
                    balance=bal_pence,
                    kind="txn",
                )
            )
        elif profile.multiline_description and rows and rows[-1].kind == "txn" and desc_cell and not has_movement:
            # Continuation of the previous transaction's description.
            prev = rows[-1]
            prev.description = (prev.description + " " + desc_cell).strip()

    return rows, centers
