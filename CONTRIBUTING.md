# Contributing

This repo is a reviewer-facing, confidentiality-safe reference build of the
RemaNet LCA matching pipeline. Contributions are welcome, especially:

- Additional synthetic process-description / sector mappings in
  `data/synthetic/knowledge_base.yaml`
- A working LLM backend implementation (`src/remanet_lca/llm_fallback.py`)
  tested against a local Ollama model
- Bug reports on the matching ladder logic in `src/remanet_lca/pipeline.py`

## Development setup

```bash
pip install -r requirements.txt
pytest -q
```

## Before opening a PR

- Run `pytest -q` and make sure it passes.
- Do not add any real partner company data, confidential process inventory
  data, or licensed database content (EXIOBASE, ecoinvent, BAFU, etc.) to
  this repository. Synthetic examples only.
- Keep PRs focused — one change per PR is easier to review.

## Questions about the paper

Please open an issue rather than emailing about reproducibility questions
tied to the CIRP LCE 2027 submission itself; issues are easier to track and
link back to.
