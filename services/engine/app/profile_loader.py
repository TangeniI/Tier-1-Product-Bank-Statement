"""Load YAML bank profiles and auto-match one to a statement's text."""
from __future__ import annotations

import re
from dataclasses import dataclass
from functools import lru_cache

import yaml

from .config import PROFILES_DIR


@dataclass(frozen=True)
class BankProfile:
    name: str
    label: str
    priority: int
    match: tuple[str, ...]
    date_formats: tuple[str, ...]
    columns: dict[str, tuple[str, ...]]
    amount: dict
    multiline_description: bool
    opening_balance_markers: tuple[str, ...]
    closing_balance_markers: tuple[str, ...]

    @staticmethod
    def from_dict(d: dict) -> "BankProfile":
        cols = {k: tuple(v) for k, v in (d.get("columns") or {}).items()}
        return BankProfile(
            name=d["name"],
            label=d.get("label", d["name"]),
            priority=int(d.get("priority", 0)),
            match=tuple(d.get("match") or ()),
            date_formats=tuple(d.get("date_formats") or ()),
            columns=cols,
            amount=dict(d.get("amount") or {}),
            multiline_description=bool(d.get("multiline_description", True)),
            opening_balance_markers=tuple(d.get("opening_balance_markers") or ()),
            closing_balance_markers=tuple(d.get("closing_balance_markers") or ()),
        )


@lru_cache(maxsize=1)
def load_profiles() -> list[BankProfile]:
    profiles: list[BankProfile] = []
    for path in sorted(PROFILES_DIR.glob("*.yaml")):
        with path.open("r", encoding="utf-8") as fh:
            data = yaml.safe_load(fh)
        profiles.append(BankProfile.from_dict(data))
    return profiles


def get_generic_profile() -> BankProfile:
    for p in load_profiles():
        if p.name == "generic":
            return p
    raise RuntimeError("generic.yaml profile is required but was not found")


def match_profile(document_text: str) -> BankProfile:
    """Pick the highest-priority profile whose `match` regexes hit the text.

    Falls back to the generic profile when nothing matches.
    """
    candidates: list[BankProfile] = []
    for profile in load_profiles():
        if not profile.match:
            continue
        for pattern in profile.match:
            if re.search(pattern, document_text, re.IGNORECASE):
                candidates.append(profile)
                break
    if not candidates:
        return get_generic_profile()
    return max(candidates, key=lambda p: p.priority)
