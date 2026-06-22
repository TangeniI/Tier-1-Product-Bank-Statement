"""Engine configuration — env-driven, with sensible defaults."""
from __future__ import annotations

import os
from pathlib import Path

APP_DIR = Path(__file__).resolve().parent
PROFILES_DIR = APP_DIR / "profiles"
PRESETS_DIR = APP_DIR / "presets"

# Max pages accepted per upload (cost + abuse guard).
MAX_PAGES = int(os.environ.get("ENGINE_MAX_PAGES", "20"))

# Reconciliation tolerance in pence. Real statements occasionally round; 1p
# absorbs nothing meaningful but keeps exact-match strictness as the default.
RECONCILE_TOLERANCE_PENCE = int(os.environ.get("ENGINE_RECONCILE_TOLERANCE_PENCE", "1"))

# Heuristic: minimum average extracted characters per page to consider a PDF as
# having a real text layer (below this we treat it as scanned → OCR path).
MIN_CHARS_PER_PAGE_FOR_TEXT_LAYER = 50
