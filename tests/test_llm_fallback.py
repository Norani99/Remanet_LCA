"""Tests for the LLM backend wiring itself (mocked HTTP, no real server needed).

These exist because connecting a real Ollama instance or cloud API is the
main thing external users will do with this repo; the request/response
parsing has to actually work, not just look plausible.
"""
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from remanet_lca.llm_fallback import LLMMatcher
from remanet_lca.pipeline import MatchingPipeline


def _mock_response(json_body, status_ok=True):
    resp = MagicMock()
    resp.json.return_value = json_body
    if status_ok:
        resp.raise_for_status = MagicMock()
    else:
        resp.raise_for_status.side_effect = Exception("HTTP error")
    return resp


@patch("requests.post")
def test_ollama_backend_parses_response(mock_post):
    mock_post.return_value = _mock_response(
        {"response": '{"sector_code": "EXIO_C27_1", "confidence": 0.91}'}
    )
    matcher = LLMMatcher(backend="ollama", confidence_threshold=0.7, model="qwen2.5:7b",
                          base_url="http://localhost:11434")
    result = matcher.match("rewire a transformer coil", ["EXIO_C27_1", "BAFU_METAL_GRIND"])
    assert result.sector_code == "EXIO_C27_1"
    assert result.confidence == 0.91
    # Confirms we actually hit the documented Ollama endpoint shape.
    called_url = mock_post.call_args[0][0]
    assert called_url.endswith("/api/generate")


@patch("requests.post")
def test_openai_compatible_backend_parses_response(mock_post, monkeypatch):
    monkeypatch.setenv("LLM_API_KEY", "test-key")
    mock_post.return_value = _mock_response(
        {"choices": [{"message": {"content": '{"sector_code": "BAFU_METAL_GRIND", "confidence": 0.88}'}}]}
    )
    matcher = LLMMatcher(backend="openai_compatible", confidence_threshold=0.7, model="gpt-4o-mini",
                          base_url="https://api.openai.com/v1", api_key_env="LLM_API_KEY")
    result = matcher.match("grind down a worn part", ["BAFU_METAL_GRIND"])
    assert result.sector_code == "BAFU_METAL_GRIND"
    assert result.confidence == 0.88
    headers = mock_post.call_args[1]["headers"]
    assert headers["Authorization"] == "Bearer test-key"


@patch("requests.post")
def test_llm_response_missing_json_escalates_cleanly(mock_post):
    mock_post.return_value = _mock_response({"response": "I'm not sure, sorry."})
    matcher = LLMMatcher(backend="ollama", confidence_threshold=0.7)
    result = matcher.match("some unparseable case", ["EXIO_C27_1"])
    assert result.sector_code is None
    assert result.confidence == 0.0


@patch("requests.post")
def test_pipeline_does_not_crash_when_backend_unreachable(mock_post):
    mock_post.side_effect = ConnectionError("Ollama is not running")
    pipeline = MatchingPipeline()
    pipeline.config["llm"]["enabled"] = True
    pipeline.llm = LLMMatcher(backend="ollama", confidence_threshold=0.7)

    # A description the cache/KB/semantic rungs cannot resolve, so it falls
    # through to the (unreachable) LLM rung.
    result = pipeline.match("a totally novel process nobody has described before")
    assert result.rung == "needs_input"
    assert result.sector_code is None
