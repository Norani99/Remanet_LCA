# RemaNet LCA — Federated LLM-Assisted Life Cycle Assessment

[![tests](https://github.com/Norani99/Remanet_LCA/actions/workflows/tests.yml/badge.svg)](https://github.com/Norani99/Remanet_LCA/actions/workflows/tests.yml)

Reference implementation of the matching pipeline described in the RemaNet paper
("LLMs as a standardisation layer for multi-stakeholder LCA in remanufacturing
networks", submitted to CIRP LCE 2027). It lets remanufacturing-network actors
contribute comparable environmental (GWP) indicators without disclosing their
confidential process inventory data.

This repository is a **cleaned-up, confidentiality-safe rebuild** of the
pipeline for reviewers and other researchers to inspect and reuse. It ships
with **synthetic example data only** — no partner company data, no original
benchmark inputs. Results from this repo will not reproduce the paper's
headline numbers; it exists to make the matching logic auditable, not to
replicate the full evaluation.

## What it does

Given a free-text description of a remanufacturing process step (e.g. "clean
and regrind a worn HSS twist drill"), the pipeline resolves it to a background
LCA database sector and returns a cradle-to-gate GWP (kg CO2-eq) figure,
without the contributing actor ever sharing raw process inventory data.

Matching proceeds through a **hybrid ladder**, cheapest and most transparent
first:

1. **Exact cache** — an identical description seen before returns its cached
   match instantly.
2. **Domain knowledge base** — a curated lookup of known process-to-sector
   mappings for the remanufacturing domain.
3. **Semantic search** — MiniLM sentence embeddings find the closest known
   description above a similarity threshold.
4. **LLM fallback** — only when the above are inconclusive, a language model
   proposes a sector match with a confidence score.

If no step clears a confidence threshold, the pipeline does **not** guess: it
returns a `NEEDS_INPUT` gate so an expert can resolve the match. This
escalation path is the core design idea — silent low-confidence matches are
treated as a correctness failure, not a usability one.

## Background databases

The matcher resolves to sector codes in:

- **EXIOBASE 3** (monetary MRIO)
- **BAFU:2026** (Swiss federal LCI)

This repo ships small synthetic stand-ins for both (`data/background_db/`) so
the pipeline runs end-to-end without a licensed database. Swap in the real
databases by implementing `BackgroundDatabase` in
`src/remanet_lca/background_db.py`.

## Install

```bash
pip install -r requirements.txt
```

Python 3.10+. An LLM backend is optional — the pipeline works with local
Ollama models or any OpenAI-compatible API; set the backend in
`config.yaml` or disable the LLM step entirely to run cache + KB + semantic
search only.

## Usage

```bash
python -m remanet_lca.pipeline --input data/synthetic/example_processes.csv --output results.csv
```

Or from Python:

```python
from remanet_lca.pipeline import MatchingPipeline

pipeline = MatchingPipeline()
result = pipeline.match("clean and regrind a worn HSS twist drill")
print(result)
```

## Repository layout

```
src/remanet_lca/
  cache.py           exact-match cache (rung 1)
  knowledge_base.py  curated process->sector lookups (rung 2)
  semantic_search.py MiniLM embedding search (rung 3)
  llm_fallback.py    LLM-based matching, last resort (rung 4)
  background_db.py   interface + synthetic stand-ins for EXIOBASE/BAFU
  gwp.py              GWP calculation from a resolved sector match
  pipeline.py         orchestrates the matching ladder end to end
data/synthetic/        example process descriptions, no real partner data
data/background_db/    synthetic sector tables (NOT EXIOBASE/BAFU)
tests/                  unit tests covering each matching rung
```

## Status

Actively developed alongside the RemaNet LCA paper (revision due for CIRP LCE
2027). Expect breaking changes. Issues and pull requests from reviewers are
welcome — please open an issue rather than emailing about reproducibility
questions tied to the paper itself.

## Citation

See `CITATION.cff`. If you use this pipeline, please cite the paper once
published; until then, cite the repository directly.

## License

MIT — see `LICENSE`.
