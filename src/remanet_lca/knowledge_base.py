"""Rung 2 of the matching ladder: curated domain knowledge base.

A small set of known process-description phrases mapped to sector codes.
Falls through to semantic search when no phrase matches.
"""
from __future__ import annotations

from pathlib import Path

import yaml

from .cache import normalize

KB_PATH = Path(__file__).resolve().parents[2] / "data" / "synthetic" / "knowledge_base.yaml"


class KnowledgeBase:
    def __init__(self, path: Path = KB_PATH):
        with open(path) as f:
            raw = yaml.safe_load(f)
        self._lookup: dict[str, str] = {}
        for entry in raw.get("entries", []):
            for phrase in entry["phrases"]:
                self._lookup[normalize(phrase)] = entry["sector_code"]

    def match(self, description: str) -> str | None:
        return self._lookup.get(normalize(description))

    def all_phrases(self) -> list[str]:
        return list(self._lookup.keys())
