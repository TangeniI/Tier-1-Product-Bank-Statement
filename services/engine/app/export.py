"""Assemble CSV / XLSX / OFX output, applying accounting-software preset
mappings."""
from __future__ import annotations

import hashlib
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


def _vat_split(t: Transaction, rate: float) -> tuple[Optional[float], Optional[float]]:
    """Split a gross amount into (net, VAT) at the given rate, assuming the
    amount is VAT-inclusive. Returns (None, None) when there's no amount."""
    gross = _signed_amount(t)
    if gross is None:
        return None, None
    net = round(gross / (1 + rate), 2)
    return net, round(gross - net, 2)


def _cell(t: Transaction, col: dict):
    source = col["source"]
    if source == "empty":
        return ""
    if source == "signed_amount":
        return _signed_amount(t)
    if source == "vat_net":
        return _vat_split(t, float(col.get("rate", 0.20)))[0]
    if source == "vat_amount":
        return _vat_split(t, float(col.get("rate", 0.20)))[1]
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


def _ofx_date(iso: str) -> str:
    try:
        return datetime.strptime(iso, "%Y-%m-%d").strftime("%Y%m%d")
    except ValueError:
        return datetime.now().strftime("%Y%m%d")


def _fitid(t: Transaction, idx: int, amount: float) -> str:
    """Stable per-transaction id so re-imports dedupe instead of doubling up."""
    raw = f"{t.date}|{amount}|{t.description}|{idx}"
    return hashlib.sha1(raw.encode("utf-8")).hexdigest()[:20]


def to_ofx(rows: list[Transaction], _preset_name: str = "ofx") -> bytes:
    """Build an OFX 1.0.2 (SGML) bank statement — the format QuickBooks, Xero
    and most accounting tools accept for bank imports (a .qbo file is the same
    content). Includes per-transaction FITIDs so importers can deduplicate."""
    txns = [r for r in rows if r.money_in is not None or r.money_out is not None]
    now = datetime.now().strftime("%Y%m%d%H%M%S")
    dated = [t for t in txns if t.date]
    dtstart = _ofx_date(min(t.date for t in dated)) if dated else now[:8]
    dtend = _ofx_date(max(t.date for t in dated)) if dated else now[:8]

    lines: list[str] = []
    for i, t in enumerate(txns):
        amount = round((t.money_in or 0.0) - (t.money_out or 0.0), 2)
        trntype = "CREDIT" if amount >= 0 else "DEBIT"
        name = (t.description or "Transaction")[:32]
        lines.append(
            "<STMTTRN>"
            f"<TRNTYPE>{trntype}"
            f"<DTPOSTED>{_ofx_date(t.date)}"
            f"<TRNAMT>{amount:.2f}"
            f"<FITID>{_fitid(t, i, amount)}"
            f"<NAME>{_ofx_escape(name)}"
            f"<MEMO>{_ofx_escape(t.description or '')}"
            "</STMTTRN>"
        )

    closing = next((t.balance for t in reversed(txns) if t.balance is not None), 0.0)
    body = (
        "OFXHEADER:100\r\nDATA:OFXSGML\r\nVERSION:102\r\nSECURITY:NONE\r\n"
        "ENCODING:USASCII\r\nCHARSET:1252\r\nCOMPRESSION:NONE\r\nOLDFILEUID:NONE\r\n"
        "NEWFILEUID:NONE\r\n\r\n"
        "<OFX><SIGNONMSGSRSV1><SONRS><STATUS><CODE>0<SEVERITY>INFO</STATUS>"
        f"<DTSERVER>{now}<LANGUAGE>ENG</SONRS></SIGNONMSGSRSV1>"
        "<BANKMSGSRSV1><STMTTRNRS><TRNUID>1<STATUS><CODE>0<SEVERITY>INFO</STATUS>"
        "<STMTRS><CURDEF>GBP<BANKACCTFROM><BANKID>000000<ACCTID>00000000"
        "<ACCTTYPE>CHECKING</BANKACCTFROM>"
        f"<BANKTRANLIST><DTSTART>{dtstart}<DTEND>{dtend}"
        + "".join(lines)
        + "</BANKTRANLIST>"
        f"<LEDGERBAL><BALAMT>{closing:.2f}<DTASOF>{dtend}</LEDGERBAL>"
        "</STMTRS></STMTTRNRS></BANKMSGSRSV1></OFX>"
    )
    return body.encode("ascii", errors="replace")


def _ofx_escape(s: str) -> str:
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
