"""Extraction accuracy harness.

Runs the engine over a corpus of statement fixtures and prints a per-statement
scorecard: rows extracted, how many reconcile against the running balance, the
confidence score, and whether the statement balances end to end. This is the
quantitative proof of the product's moat — extend `CORPUS` with real (anonymised)
statements per bank to track accuracy as profiles are added.

Usage:
    python scripts/eval.py            # human-readable table
    python scripts/eval.py --json     # machine-readable, for CI dashboards
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ENGINE_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ENGINE_ROOT))
sys.path.insert(0, str(ENGINE_ROOT / "scripts"))

from app.pipeline import extract  # noqa: E402
import make_fixture  # noqa: E402

# (label, builder) — builders write a synthetic PDF to a path. Swap/add real
# anonymised statements here as the bank-profile library grows.
CORPUS = [
    ("Barclays — year-bearing", make_fixture.build_pdf),
    ("Barclays — yearless dates", make_fixture.build_yearless_pdf),
    ("Barclays — Dec→Jan boundary", make_fixture.build_boundary_pdf),
    ("Starling — single Amount col", make_fixture.build_starling_pdf),
]


def evaluate(tmp: Path) -> list[dict]:
    results = []
    for i, (label, builder) in enumerate(CORPUS):
        path = tmp / f"fixture_{i}.pdf"
        builder(path)
        r = extract(path.read_bytes())
        s = r.summary
        checkable = s.movement_rows
        recon_pct = (
            100.0 * (s.movement_rows - s.flagged_rows) / checkable if checkable else 0.0
        )
        results.append(
            {
                "statement": label,
                "profile": r.bank_profile,
                "rows": len(r.rows),
                "reconciled_pct": round(recon_pct, 1),
                "flagged": s.flagged_rows,
                "confidence": round(r.overall_confidence, 4),
                "balanced": s.balanced,
            }
        )
    return results


def main() -> int:
    import tempfile

    with tempfile.TemporaryDirectory() as d:
        results = evaluate(Path(d))

    if "--json" in sys.argv:
        print(json.dumps(results, indent=2))
        return 0

    print(f"\n  Tabular extraction scorecard — {len(results)} statements\n")
    header = f"  {'Statement':<30}{'Profile':<12}{'Rows':>5}{'Recon%':>8}{'Flag':>5}{'Conf':>7}{'Bal':>5}"
    print(header)
    print("  " + "-" * (len(header) - 2))
    for r in results:
        print(
            f"  {r['statement']:<30}{r['profile']:<12}{r['rows']:>5}"
            f"{r['reconciled_pct']:>8}{r['flagged']:>5}{r['confidence']:>7}"
            f"{'  ✓' if r['balanced'] else '  ✗':>5}"
        )
    avg = sum(r["reconciled_pct"] for r in results) / len(results)
    print(f"\n  Mean reconciliation rate: {avg:.1f}%\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
