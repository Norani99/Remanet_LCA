"""Rung 4 of the matching ladder: LLM-based matching, last resort.

Only reached when cache, knowledge base, and semantic search all fail to
resolve a confident match. The LLM proposes a sector code and a confidence
score; below the confidence threshold the pipeline escalates to NEEDS_INPUT
rather than accepting a low-confidence guess.

No backend is wired up by default (backend="none"): this module defines the
interface and a stub that always escalates, so the repo runs without API
keys or a local model. Point `config.yaml`'s llm.backend at "ollama" or
"openai_compatible" and implement `_call_backend` for your environment.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass
class LLMMatchResult:
    sector_code: str | None
    confidence: float
    raw_response: str = ""


class LLMMatcher:
    def __init__(self, backend: str = "none", confidence_threshold: float = 0.70, **kwargs):
        self.backend = backend
        self.confidence_threshold = confidence_threshold
        self._kwargs = kwargs

    def match(self, description: str, candidate_sectors: list[str]) -> LLMMatchResult:
        if self.backend == "none":
            # No backend configured: always escalate rather than guess.
            return LLMMatchResult(sector_code=None, confidence=0.0, raw_response="backend disabled")
        return self._call_backend(description, candidate_sectors)

    def _call_backend(self, description: str, candidate_sectors: list[str]) -> LLMMatchResult:
        if self.backend == "ollama":
            return self._call_ollama(description, candidate_sectors)
        if self.backend == "openai_compatible":
            return self._call_openai_compatible(description, candidate_sectors)
        raise ValueError(f"Unknown LLM backend: {self.backend}")

    def _call_ollama(self, description: str, candidate_sectors: list[str]) -> LLMMatchResult:
        import json

        import requests

        prompt = _build_prompt(description, candidate_sectors)
        resp = requests.post(
            f"{self._kwargs.get('base_url', 'http://localhost:11434')}/api/generate",
            json={"model": self._kwargs.get("model", "qwen2.5:7b"), "prompt": prompt, "stream": False},
            timeout=60,
        )
        resp.raise_for_status()
        text = resp.json().get("response", "")
        return _parse_llm_json(text)

    def _call_openai_compatible(self, description: str, candidate_sectors: list[str]) -> LLMMatchResult:
        import os

        import requests

        prompt = _build_prompt(description, candidate_sectors)
        api_key = os.environ.get(self._kwargs.get("api_key_env", "LLM_API_KEY"), "")
        resp = requests.post(
            f"{self._kwargs.get('base_url')}/chat/completions",
            headers={"Authorization": f"Bearer {api_key}"},
            json={
                "model": self._kwargs.get("model"),
                "messages": [{"role": "user", "content": prompt}],
            },
            timeout=60,
        )
        resp.raise_for_status()
        text = resp.json()["choices"][0]["message"]["content"]
        return _parse_llm_json(text)


def _build_prompt(description: str, candidate_sectors: list[str]) -> str:
    return (
        "You match a remanufacturing process description to the closest LCA "
        "background sector code. Respond ONLY with JSON: "
        '{"sector_code": "<code or null>", "confidence": <0-1 float>}.\n\n'
        f"Process description: {description}\n"
        f"Candidate sector codes: {candidate_sectors}\n"
    )


def _parse_llm_json(text: str) -> LLMMatchResult:
    import json
    import re

    match = re.search(r"\{.*\}", text, re.DOTALL)
    if not match:
        return LLMMatchResult(sector_code=None, confidence=0.0, raw_response=text)
    try:
        obj = json.loads(match.group(0))
        return LLMMatchResult(
            sector_code=obj.get("sector_code"),
            confidence=float(obj.get("confidence", 0.0)),
            raw_response=text,
        )
    except (json.JSONDecodeError, TypeError, ValueError):
        return LLMMatchResult(sector_code=None, confidence=0.0, raw_response=text)
