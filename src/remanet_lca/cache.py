"""Rung 1 of the matching ladder: exact-match cache.

A description that has already been resolved (verbatim, after normalization)
returns its cached sector code instantly, with no LLM call and no inventory
data leaving the actor's system.
"""
from __future__ import annotations


def normalize(text: str) -> str:
    return " ".join(text.strip().lower().split())


class ExactMatchCache:
    def __init__(self):
        self._store: dict[str, str] = {}

    def get(self, description: str) -> str | None:
        return self._store.get(normalize(description))

    def put(self, description: str, sector_code: str) -> None:
        self._store[normalize(description)] = sector_code

    def __len__(self) -> int:
        return len(self._store)
