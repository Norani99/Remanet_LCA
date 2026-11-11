"""Orchestrates the hybrid matching ladder: cache -> KB -> semantic -> LLM -> NEEDS_INPUT."""
from __future__ import annotations

import argparse
from dataclasses import dataclass, asdict
from pathlib import Path

import pandas as pd
import yaml

from .background_db import BackgroundDatabase
from .cache import ExactMatchCache
from .gwp import compute_gwp
from .knowledge_base import KnowledgeBase
from .llm_fallback import LLMMatcher
from .semantic_search import SemanticMatcher

CONFIG_PATH = Path(__file__).resolve().parents[2] / "config.yaml"


@dataclass
class MatchResult:
    process_description: str
    sector_code: str | None
    rung: str  # "cache" | "knowledge_base" | "semantic" | "llm" | "needs_input"
    confidence: float
    gwp_kg_co2e_per_unit: float | None


class MatchingPipeline:
    def __init__(self, config_path: Path = CONFIG_PATH):
        with open(config_path) as f:
            self.config = yaml.safe_load(f)

        self.cache = ExactMatchCache()
        self.kb = KnowledgeBase()
        self.semantic = SemanticMatcher(
            model_name=self.config["embeddings"]["model"],
            threshold=self.config["matching"]["semantic_similarity_threshold"],
        )
        llm_cfg = self.config["llm"]
        self.llm = LLMMatcher(
            backend=llm_cfg["backend"],
            confidence_threshold=self.config["matching"]["llm_confidence_threshold"],
            model=llm_cfg.get("model"),
            base_url=llm_cfg.get("base_url"),
            api_key_env=llm_cfg.get("api_key_env"),
        )
        self.db = BackgroundDatabase()

        # Build the phrase->sector map once for semantic search.
        self._phrase_to_sector = {p: self.kb.match(p) for p in self.kb.all_phrases()}

    def match(self, description: str) -> MatchResult:
        # Rung 1: exact cache
        cached = self.cache.get(description)
        if cached:
            return self._finalize(description, cached, "cache", confidence=1.0)

        # Rung 2: domain knowledge base
        kb_hit = self.kb.match(description)
        if kb_hit:
            self.cache.put(description, kb_hit)
            return self._finalize(description, kb_hit, "knowledge_base", confidence=1.0)

        # Rung 3: semantic search over KB phrases
        semantic_hit = self.semantic.match(description, self._phrase_to_sector)
        if semantic_hit:
            sector_code, similarity = semantic_hit
            self.cache.put(description, sector_code)
            return self._finalize(description, sector_code, "semantic", confidence=similarity)

        # Rung 4: LLM fallback
        if self.config["llm"]["enabled"]:
            candidates = [s.sector_code for s in self.db.all_sectors()]
            llm_result = self.llm.match(description, candidates)
            if llm_result.sector_code and llm_result.confidence >= self.llm.confidence_threshold:
                self.cache.put(description, llm_result.sector_code)
                return self._finalize(
                    description, llm_result.sector_code, "llm", confidence=llm_result.confidence
                )

        # No rung resolved a confident match: escalate rather than guess.
        return MatchResult(
            process_description=description,
            sector_code=None,
            rung="needs_input",
            confidence=0.0,
            gwp_kg_co2e_per_unit=None,
        )

    def _finalize(self, description: str, sector_code: str, rung: str, confidence: float) -> MatchResult:
        try:
            sector = self.db.get(sector_code)
            gwp_per_unit = sector.gwp_kg_co2e_per_unit
        except KeyError:
            gwp_per_unit = None
        return MatchResult(
            process_description=description,
            sector_code=sector_code,
            rung=rung,
            confidence=confidence,
            gwp_kg_co2e_per_unit=gwp_per_unit,
        )


def run_batch(input_csv: Path, output_csv: Path) -> None:
    pipeline = MatchingPipeline()
    df = pd.read_csv(input_csv)
    results = pd.DataFrame(
        [asdict(pipeline.match(desc)) for desc in df["process_description"]]
    ).drop(columns=["process_description"])
    out = pd.concat([df.reset_index(drop=True), results], axis=1)

    # If the input gives a quantity per step, scale the per-unit GWP figure
    # into a total for that step so steps can be summed into a case total.
    if "quantity" in out.columns:
        out["gwp_kg_co2e_total"] = out["gwp_kg_co2e_per_unit"] * out["quantity"]

    out.to_csv(output_csv, index=False)
    n_resolved = (out["rung"] != "needs_input").sum()
    print(f"Resolved {n_resolved}/{len(out)} process steps. Wrote {output_csv}")

    if "case" in out.columns and "gwp_kg_co2e_total" in out.columns:
        print("\nTotal GWP by case (resolved steps only, kg CO2-eq):")
        totals = out.groupby("case")["gwp_kg_co2e_total"].sum(min_count=1)
        for case, total in totals.items():
            print(f"  {case}: {total:.3f}")


def main():
    parser = argparse.ArgumentParser(description="RemaNet LCA matching pipeline")
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    run_batch(args.input, args.output)


if __name__ == "__main__":
    main()
