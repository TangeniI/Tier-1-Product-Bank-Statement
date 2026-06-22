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
    min_matches: int
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
            min_matches=int(d.get("min_matches", 1)),
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
    """Pick the best profile for a statement.

    A profile qualifies only when at least `min_matches` of its distinct `match`
    patterns hit the text — so a stray mention of a bank's name in a transaction
    line (e.g. "payment to Barclays" on a Monzo statement) doesn't misclassify
    the whole document. Among qualifiers we maximise (priority, match count);
    nothing qualifying falls back to the generic profile.
    """
    scored: list[tuple[int, int, BankProfile]] = []
    for profile in load_profiles():
        if not profile.match:
            continue
        hits = sum(
            1 for pattern in profile.match
            if re.search(pattern, document_text, re.IGNORECASE)
        )
        if hits >= profile.min_matches:
            scored.append((profile.priority, hits, profile))
    if not scored:
        return get_generic_profile()
    return max(scored, key=lambda s: (s[0], s[1]))[2]
