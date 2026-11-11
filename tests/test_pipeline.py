"""Unit tests covering each rung of the matching ladder on synthetic data."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from remanet_lca.cache import ExactMatchCache, normalize
from remanet_lca.knowledge_base import KnowledgeBase
from remanet_lca.background_db import BackgroundDatabase
from remanet_lca.gwp import compute_gwp
from remanet_lca.pipeline import MatchingPipeline


def test_normalize():
    assert normalize("  Clean and Regrind  ") == "clean and regrind"


def test_exact_cache_roundtrip():
    cache = ExactMatchCache()
    cache.put("Regrind the drill", "BAFU_METAL_GRIND")
    assert cache.get("regrind the drill") == "BAFU_METAL_GRIND"
    assert cache.get("unseen description") is None


def test_knowledge_base_known_phrase():
    kb = KnowledgeBase()
    assert kb.match("regrind a worn hss twist drill") == "BAFU_METAL_GRIND"
    assert kb.match("completely unrelated phrase") is None


def test_background_db_lookup():
    db = BackgroundDatabase()
    sector = db.get("BAFU_METAL_GRIND")
    assert sector.sector_name == "Grinding and resharpening of tool steel"
    assert sector.gwp_kg_co2e_per_unit == 0.62


def test_gwp_calculation():
    db = BackgroundDatabase()
    sector = db.get("BAFU_METAL_GRIND")
    result = compute_gwp(sector, quantity=2.5)
    assert result.gwp_kg_co2e == 1.55


def test_pipeline_resolves_known_phrase_via_knowledge_base():
    pipeline = MatchingPipeline()
    result = pipeline.match("clean and regrind a worn HSS twist drill")
    assert result.rung in ("knowledge_base", "cache")
    assert result.sector_code == "BAFU_METAL_GRIND"


def test_pipeline_escalates_unresolvable_description():
    pipeline = MatchingPipeline()
    result = pipeline.match("completely unknown process with no match at all xyz123")
    assert result.rung == "needs_input"
    assert result.sector_code is None


def test_pipeline_caches_after_first_resolution():
    pipeline = MatchingPipeline()
    first = pipeline.match("recycle scrap tungsten carbide")
    assert first.rung == "knowledge_base"
    second = pipeline.match("recycle scrap tungsten carbide")
    assert second.rung == "cache"
    assert second.sector_code == first.sector_code
