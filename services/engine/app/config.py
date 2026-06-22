"""Engine configuration — env-driven, with sensible defaults."""
from __future__ import annotations

import os
from pathlib import Path

APP_DIR = Path(__file__).resolve().parent
PROFILES_DIR = APP_DIR / "profiles"
PRESETS_DIR = APP_DIR / "presets"

# Max pages accepted per upload (cost + abuse guard).
MAX_PAGES = int(os.environ.get("ENGINE_MAX_PAGES", "20"))

# Max rows accepted on the /export endpoint (abuse guard for the edited payload).
MAX_EXPORT_ROWS = int(os.environ.get("ENGINE_MAX_EXPORT_ROWS", "10000"))

# Allowed CORS origins, comma-separated. Defaults to "*" for local dev; set to
# the app origin(s) in production (e.g. "https://app.tabular.example").
ALLOWED_ORIGINS = [
    o.strip() for o in os.environ.get("ENGINE_ALLOWED_ORIGINS", "*").split(",") if o.strip()
]

# Reconciliation tolerance in pence. Real statements occasionally round; 1p
# absorbs nothing meaningful but keeps exact-match strictness as the default.
RECONCILE_TOLERANCE_PENCE = int(os.environ.get("ENGINE_RECONCILE_TOLERANCE_PENCE", "1"))

# Heuristic: minimum average extracted characters per page to consider a PDF as
# having a real text layer (below this we treat it as scanned → OCR path).
MIN_CHARS_PER_PAGE_FOR_TEXT_LAYER = 50
