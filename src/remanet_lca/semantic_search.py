"""Rung 3 of the matching ladder: MiniLM semantic search.

Embeds the incoming description and the known knowledge-base phrases, and
returns the closest phrase's sector code if cosine similarity clears the
configured threshold. Falls through to the LLM otherwise.

The sentence-transformers dependency is imported lazily so the rest of the
pipeline (cache, KB, GWP calc) works without it installed.
"""
from __future__ import annotations


class SemanticMatcher:
    def __init__(self, model_name: str = "all-MiniLM-L6-v2", threshold: float = 0.75):
        self.threshold = threshold
        self._model_name = model_name
        self._model = None  # lazy-loaded

    def _load_model(self):
        if self._model is None:
            from sentence_transformers import SentenceTransformer

            self._model = SentenceTransformer(self._model_name)
        return self._model

    def match(self, description: str, phrase_to_sector: dict[str, str]) -> tuple[str, float] | None:
        if not phrase_to_sector:
            return None
        try:
            model = self._load_model()
        except ImportError:
            return None

        from sklearn.metrics.pairwise import cosine_similarity

        phrases = list(phrase_to_sector.keys())
        embeddings = model.encode(phrases + [description])
        phrase_vecs, query_vec = embeddings[:-1], embeddings[-1:]
        sims = cosine_similarity(query_vec, phrase_vecs)[0]
        best_idx = int(sims.argmax())
        best_sim = float(sims[best_idx])
        if best_sim >= self.threshold:
            return phrase_to_sector[phrases[best_idx]], best_sim
        return None
