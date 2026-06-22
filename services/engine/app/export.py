"""Assemble CSV / XLSX output, applying accounting-software preset mappings."""
from __future__ import annotations

import io
from dataclasses import dataclass
from datetime import datetime
from functools import lru_cache
from typing import Optional

import pandas as pd
import yaml

from .config import PRESETS_DIR
from .schema import Transaction


@dataclass(frozen=True)
class Preset:
    name: str
    label: str
    transactions_only: bool
    columns: tuple[dict, ...]


@lru_cache(maxsize=1)
def load_presets() -> dict[str, Preset]:
    presets: dict[str, Preset] = {}
    for path in sorted(PRESETS_DIR.glob("*.yaml")):
        d = yaml.safe_load(path.read_text(encoding="utf-8"))
        presets[d["name"]] = Preset(
            name=d["name"],
            label=d.get("label", d["name"]),
            transactions_only=bool(d.get("transactions_only", False)),
            columns=tuple(d.get("columns") or ()),
        )
    return presets


def list_presets() -> list[dict[str, str]]:
    return [{"name": p.name, "label": p.label} for p in load_presets().values()]


def _signed_amount(t: Transaction) -> Optional[float]:
    if t.money_in is None and t.money_out is None:
        return None
    return round((t.money_in or 0.0) - (t.money_out or 0.0), 2)


def _cell(t: Transaction, col: dict):
    source = col["source"]
    if source == "empty":
        return ""
    if source == "signed_amount":
        return _signed_amount(t)
    if source == "date":
        fmt = col.get("date_format")
        if fmt and t.date:
            try:
                return datetime.strptime(t.date, "%Y-%m-%d").strftime(fmt)
            except ValueError:
                return t.date
        return t.date
    return getattr(t, source, None)


def build_dataframe(rows: list[Transaction], preset_name: str) -> pd.DataFrame:
    presets = load_presets()
    preset = presets.get(preset_name) or presets["default"]
    selected = (
        [r for r in rows if r.money_in is not None or r.money_out is not None]
        if preset.transactions_only
        else rows
    )
    data = {
        col["header"]: [_cell(t, col) for t in selected] for col in preset.columns
    }
    return pd.DataFrame(data, columns=[c["header"] for c in preset.columns])


def to_csv(rows: list[Transaction], preset_name: str) -> bytes:
    df = build_dataframe(rows, preset_name)
    return df.to_csv(index=False).encode("utf-8")


def to_xlsx(rows: list[Transaction], preset_name: str) -> bytes:
    df = build_dataframe(rows, preset_name)
    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Transactions")
    return buf.getvalue()
