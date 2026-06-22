"""Deterministic keyword categorisation for transactions.

Bookkeepers spend most of their statement-cleanup time assigning each line to a
nominal/category code. A rules table (categories.yaml — data, not code) gives a
sensible first pass that the user can correct inline. The rules are ordered:
the first category with a matching keyword wins.

This is intentionally a transparent v1. A classifier that learns from the user's
corrections is the natural next step, but a rules engine is auditable and needs
no training data to be useful on day one.
"""
from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache

import yaml

from .config import APP_DIR

CATEGORIES_PATH = APP_DIR / "categories.yaml"


@dataclass(frozen=True)
class CategoryRule:
    category: str
    keywords: tuple[str, ...]


@lru_cache(maxsize=1)
def load_rules() -> tuple[CategoryRule, ...]:
    data = yaml.safe_load(CATEGORIES_PATH.read_text(encoding="utf-8")) or {}
    return tuple(
        CategoryRule(r["category"], tuple(k.lower() for k in r.get("keywords", [])))
        for r in data.get("rules", [])
    )


def categorize(description: str) -> str | None:
    """Return the first matching category for a description, or None."""
    if not description:
        return None
    low = description.lower()
    for rule in load_rules():
        if any(kw in low for kw in rule.keywords):
            return rule.category
    return None
