"""Export presets produce the right columns and signed amounts."""
import io

import pandas as pd

from app.export import build_dataframe, list_presets, to_csv, to_ofx, to_xlsx
from app.schema import Transaction

ROWS = [
    Transaction(date="2026-04-02", description="TESCO", money_out=45.50, balance=954.50),
    Transaction(date="2026-04-05", description="Salary", money_in=2000.00, balance=2954.50),
]


def test_presets_listed():
    names = {p["name"] for p in list_presets()}
    assert {"default", "xero", "quickbooks", "freeagent"} <= names


def test_default_preset_columns():
    df = build_dataframe(ROWS, "default")
    assert list(df.columns) == [
        "Date", "Description", "Category", "Money In", "Money Out", "Balance"
    ]


def test_xero_signed_amount_and_date_format():
    df = build_dataframe(ROWS, "xero")
    assert list(df.columns) == ["Date", "Amount", "Payee", "Description", "Reference"]
    assert df.iloc[0]["Date"] == "02/04/2026"
    assert df.iloc[0]["Amount"] == -45.50  # money out → negative
    assert df.iloc[1]["Amount"] == 2000.00


def test_csv_and_xlsx_roundtrip():
    csv_bytes = to_csv(ROWS, "quickbooks")
    assert b"Date,Description,Amount" in csv_bytes.split(b"\n")[0] + b","

    xlsx_bytes = to_xlsx(ROWS, "default")
    df = pd.read_excel(io.BytesIO(xlsx_bytes))
    assert len(df) == 2


def test_ofx_structure_and_signed_amounts():
    ofx = to_ofx(ROWS).decode("ascii")
    assert "OFXHEADER:100" in ofx
    assert "<TRNTYPE>DEBIT" in ofx  # money out
    assert "<TRNTYPE>CREDIT" in ofx  # money in
    assert "<TRNAMT>-45.50" in ofx
    assert "<TRNAMT>2000.00" in ofx
    assert "<DTPOSTED>20260402" in ofx
    # One FITID per transaction, all distinct (lets importers dedupe).
    fitids = [ln for ln in ofx.split("<FITID>")[1:]]
    assert len({f[:20] for f in fitids}) == 2
    assert "&amp;" not in ofx  # no unescaped entities issues here

    ofx_amp = to_ofx([Transaction(date="2026-04-02", description="A & B Ltd", money_in=10.0)])
    assert "A &amp; B Ltd" in ofx_amp.decode("ascii")
