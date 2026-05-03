# docink — agent instructions

This file orients an LLM agent (Claude Code, Cursor, Cline, etc.) working in
this repo. Humans should read [README.md](README.md) and
[docs/architecture.md](docs/architecture.md) first.

## What docink is

A thin schema layer over existing best-in-class extractors (defuddle, docling,
markitdown, yt-dlp). It owns three things: stable IDs, addressable chunks,
and uniform frontmatter. It does **not** own the extraction logic — that's
delegated to backends.

The whole library should stay small. If you find yourself adding a feature
that another tool already does, wrap that tool instead.

## Where to make changes

| You want to... | Edit |
|---|---|
| Add a new source type | `src/docink/adapters/<name>.py` + register in `registry.py` |
| Change the output schema | `src/docink/core.py` (`Document`, `Chunk`) |
| Change ID strategy | `src/docink/ids.py` |
| Change chunking | `src/docink/chunking.py` |
| Add a CLI flag | `src/docink/cli.py` |
| Add an MCP tool | `src/docink/mcp/server.py` |

Don't touch tests under `.pytest_cache/` or anything in `.venv/`.

## Invariants — do not break

1. `extract(uri)` is idempotent on `id`. Same URI in → same `id` out.
2. Chunk IDs are positional (`c0`, `c1`, ...) and stable as long as document
   structure is stable. Drift is detected via `content_hash`.
3. Adapters return a flat dict (not a `Document`); the core wraps it. This
   keeps adapters trivial to test and swap.
4. Each adapter is one file. No shared adapter base class — duplication is
   cheaper than coupling for four small wrappers.
5. Core has only one runtime dependency: `pyyaml`. Heavy extractors live
   behind optional extras (`docink[web]`, `docink[pdf]`, etc.).

## Common tasks

### Add a new adapter

1. Create `src/docink/adapters/<name>.py` with one function:
   ```python
   def extract(uri: str) -> dict[str, Any]: ...
   ```
   Return keys: `markdown`, `title`, `author`, `published_at`, `language`,
   `extractor`, `extras`.
2. Add the source-type detection branch in `src/docink/registry.py`.
3. Add the dependency under a new extras group in `pyproject.toml`.
4. Add a golden fixture under `tests/fixtures/<name>/` and a unit test that
   reads it (no network).
5. Document the adapter in [docs/adapters.md](docs/adapters.md).

Full contract: [docs/adapters.md](docs/adapters.md).

### Run the test suite

```bash
.venv/bin/pytest -q
```

The fast path. No network. All 10 baseline tests should pass.

### Try the CLI

```bash
.venv/bin/docink ./README.md          # dispatched as web (markdown is treated as html)
.venv/bin/docink <youtube-url>        # needs `pip install -e .[youtube]`
.venv/bin/docink <pdf-url> --json
.venv/bin/docink <url> --out ./out/   # writes <id>.md + <id>.chunks.jsonl
```

## Style rules

- Type hints on every function signature.
- No `print()` outside the CLI.
- No comments describing *what* the code does — only *why* (when non-obvious).
- Standard library before adding a dep. New deps need a one-line justification
  in the PR description.

## Pitfalls

- **Don't read the URL twice.** The adapter fetches once; the core hashes the
  returned markdown. If you re-fetch in the core for hashing, you'll get a
  different `content_hash` than the body the user receives.
- **Heading paths reset on H2.** The chunker splits at H2 by default. If you
  add an H3-aware mode, gate it behind a `strategy=` parameter — don't change
  the default.
- **`canonical_uri` for files resolves to absolute paths.** Two checkouts of
  the same file at different paths produce different `id`s. This is intentional
  (filesystem identity beats content identity for ingest tracking).

## When unsure, prefer

- Smaller diffs over larger ones.
- Wrapping an existing tool over rolling your own.
- Failing loudly with a clear error and install hint over silent fallback.
- One file per adapter over a clever class hierarchy.
