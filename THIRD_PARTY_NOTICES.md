# Third-party notices

This project (MIT licensed, see `LICENSE`) depends on the following
open-source packages. Each keeps its own license; none of them require
attribution beyond what's listed here, but it's recorded for anyone
checking license compatibility before reuse.

| Package | License | Notes |
|---|---|---|
| [pandas](https://github.com/pandas-dev/pandas) | BSD 3-Clause | tabular data handling |
| [numpy](https://github.com/numpy/numpy) | BSD 3-Clause | numerical arrays |
| [sentence-transformers](https://github.com/UKPLab/sentence-transformers) | Apache License 2.0 | MiniLM embeddings (rung 3 of the matching ladder) |
| [scikit-learn](https://github.com/scikit-learn/scikit-learn) | BSD 3-Clause | cosine similarity for semantic search |
| [PyYAML](https://github.com/yaml/pyyaml) | MIT | config and knowledge-base file parsing |
| [requests](https://github.com/psf/requests) | Apache License 2.0 | HTTP calls to Ollama / OpenAI-compatible APIs |
| [pytest](https://github.com/pytest-dev/pytest) | MIT | test suite |

`sentence-transformers` in turn pulls in PyTorch (BSD 3-Clause) and
Hugging Face `transformers`/`tokenizers` (Apache License 2.0) as transitive
dependencies when installed. Run `pip-licenses` (`pip install pip-licenses`)
in your environment for a complete, up-to-date transitive list if you need
one for a formal license audit.

## Background databases

The synthetic stand-ins in `data/background_db/` are original, made-up
example tables written for this repository — they are not extracted from
EXIOBASE 3 or BAFU:2026, and carry no license obligation from either. If
you swap in the real EXIOBASE 3 or BAFU:2026 databases via
`src/remanet_lca/background_db.py`, follow each database's own license and
attribution terms (EXIOBASE is released under the EXIOBASE licence
allowing free use with attribution; the Swiss Federal Office for the
Environment, FOEN/BAFU, sets its own terms of use for BAFU LCI data).
