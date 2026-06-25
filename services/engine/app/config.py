"""Engine configuration — env-driven, with sensible defaults."""
from __future__ import annotations

import os
from pathlib import Path

APP_DIR = Path(__file__).resolve().parent
PROFILES_DIR = APP_DIR / "profiles"
PRESETS_DIR = APP_DIR / "presets"


def _load_dotenv() -> None:
    """Minimal .env loader (no extra dependency): read services/engine/.env if
    present and populate os.environ for any keys not already set. Keeps secrets
    like GEMINI_API_KEY out of the codebase — .env is git-ignored."""
    env_path = APP_DIR.parent / ".env"
    if not env_path.exists():
        return
    for line in env_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


_load_dotenv()

# Max pages accepted per upload (cost + abuse guard).
MAX_PAGES = int(os.environ.get("ENGINE_MAX_PAGES", "20"))

# Max rows accepted on the /export endpoint (abuse guard for the edited payload).
MAX_EXPORT_ROWS = int(os.environ.get("ENGINE_MAX_EXPORT_ROWS", "10000"))

# Allowed CORS origins, comma-separated. Defaults to "*" for local dev; set to
# the app origin(s) in production (e.g. "https://app.tabular.example").
ALLOWED_ORIGINS = [
    o.strip() for o in os.environ.get("ENGINE_ALLOWED_ORIGINS", "*").split(",") if o.strip()
]

# Shared secret between the web app and the engine. CORS only restrains browsers;
# this stops anyone who finds the engine URL from calling it directly (and burning
# the LLM quota). When unset (local dev) the check is skipped. Set the SAME value
# as ENGINE_API_TOKEN on both Render and Vercel to enable it.
ENGINE_API_TOKEN = os.environ.get("ENGINE_API_TOKEN") or None

# Reconciliation tolerance in pence. Real statements occasionally round; 1p
# absorbs nothing meaningful but keeps exact-match strictness as the default.
RECONCILE_TOLERANCE_PENCE = int(os.environ.get("ENGINE_RECONCILE_TOLERANCE_PENCE", "1"))

# Heuristic: minimum average extracted characters per page to consider a PDF as
# having a real text layer (below this we treat it as scanned → OCR path).
MIN_CHARS_PER_PAGE_FOR_TEXT_LAYER = 50
