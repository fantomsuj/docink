# Contributing to docink

Thanks for considering a contribution. The bar for changes is: does this make extraction more reliable, more uniform, or more useful to an agent? If yes, open a PR.

## Dev setup

```bash
git clone https://github.com/docink/docink
cd docink
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[all,dev]"
pytest -q
```

You don't need every adapter's deps to work on the core. Use the relevant extra:

```bash
pip install -e ".[web,dev]"      # working on the web adapter
pip install -e ".[pdf,dev]"      # working on the pdf adapter
```

## Project layout

```
src/docink/
  core.py          # Document, Chunk, extract() orchestration
  ids.py           # canonical_uri, doc_id, content_hash
  registry.py      # URI → adapter dispatch
  chunking.py      # heading-aware chunker (shared by all adapters)
  cli.py           # `docink` entry point
  adapters/        # web, pdf, youtube, office (one file each)
  mcp/server.py    # FastMCP server exposing extract()
tests/             # pytest, no network in unit tests
docs/              # design docs (architecture, schema, adapters, mcp)
```

See [docs/architecture.md](docs/architecture.md) for the design rationale and [docs/adapters.md](docs/adapters.md) for the adapter contract.

## What to work on

Good first contributions:

- **New adapter** — Slack export, Gmail mbox, Notion export, GitHub repo, RSS, plain HTML file. Follow the contract in [docs/adapters.md](docs/adapters.md).
- **Adapter robustness** — better fallbacks (defuddle wrapping for `web`, docling for layout-rich PDFs), language detection, more accurate `published_at` parsing.
- **Golden fixtures** — sample sources committed under `tests/fixtures/` with expected output. Currently we have only unit tests; integration coverage is the biggest gap.
- **Chunking strategies** — the default is heading-aware at H2; semantic / size-bounded variants would be welcome behind a `strategy=` flag.

Avoid:

- Scope creep into RAG, embeddings, or storage. `docink` extracts; downstream tools index. Keeping that line clean is the value.
- Adapters for sources that need long-running auth or pagination (e.g. live Slack API, Gmail API). Prefer adapters over local exports.

## Code style

- Type hints everywhere. The library is small enough that strict typing is cheap.
- Standard library first; new dependencies need justification in the PR description.
- No comments that describe *what* the code does. Comments only for *why* (a non-obvious constraint or workaround).
- Keep adapter files self-contained — one file per source type.

## Tests

- Unit tests must not hit the network. Mock or use local fixtures.
- Integration tests that hit live URLs go behind a `pytest -m integration` marker (TODO: not wired up yet).
- Every adapter PR should include a golden fixture in `tests/fixtures/<adapter>/`.

```bash
pytest -q                        # unit tests only
pytest -m integration            # integration (when wired)
pytest --cov=docink --cov-report=term-missing
```

## Commits & PRs

- One logical change per PR. Adapter additions are independent — don't bundle.
- PR description should answer: what source does this make extractable, which backend it wraps, and what edge cases the tests cover.
- Update [CHANGELOG.md](CHANGELOG.md) under the `## [Unreleased]` section.

## Releasing (maintainers)

1. Bump version in `pyproject.toml` and `src/docink/__init__.py`.
2. Move `## [Unreleased]` entries under a new `## [x.y.z] — YYYY-MM-DD` header in `CHANGELOG.md`.
3. Tag `vX.Y.Z` and push. CI publishes to PyPI on tags (TODO: wire up).
