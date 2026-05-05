# AGENTS.md — handoff context for coding agents

This file is the entry point for an autonomous coding agent (Claude Code,
Cursor, Aider, Codex CLI, etc.) picking up work on `docink` cold. Read
this first, then [CLAUDE.md](CLAUDE.md) for the project-specific operating
rules, then [docs/architecture.md](docs/architecture.md) for the design
rationale.

## Project at a glance

- **Name:** `docink`
- **Purpose:** Wrap best-in-class extractors (defuddle, docling, markitdown,
  yt-dlp, trafilatura) behind a uniform agent-readable schema with stable
  IDs and addressable chunks.
- **Status:** v0.1 stub. Functional core, four adapters, MCP server, 10
  passing unit tests. Not yet published to PyPI or pushed to GitHub.
- **Language:** Python 3.10+
- **License:** MIT (this repo) — see [docs/licensing.md](docs/licensing.md)
  for the wrapped-backend license matrix.
- **Lives in:** `sandbox/skolpuru/docink/` of the dirt monorepo while in
  development; will be extracted to its own GitHub repo before publishing.

## What's built

| Path | What it does | State |
|---|---|---|
| `src/docink/core.py` | `Document`, `Chunk`, `extract()` orchestration | Done |
| `src/docink/ids.py` | Canonical URI normalization, doc/content hashing | Done |
| `src/docink/chunking.py` | Heading-aware chunker (splits at H2) | Done |
| `src/docink/registry.py` | URI → adapter dispatch | Done |
| `src/docink/cli.py` | `docink` CLI entry point | Done |
| `src/docink/mcp/server.py` | FastMCP stdio server with two tools | Done |
| `src/docink/adapters/web.py` | defuddle backend + trafilatura fallback | Done |
| `src/docink/adapters/pdf.py` | markitdown backend | Done |
| `src/docink/adapters/youtube.py` | yt-dlp + VTT-to-markdown | Done |
| `src/docink/adapters/office.py` | markitdown for docx/pptx/xlsx | Done |
| `tests/test_ids.py` | Unit tests for ID stability | Done (6 tests) |
| `tests/test_chunking.py` | Unit tests for chunker | Done (4 tests) |

## What's not built (in priority order)

1. **docling backend for the PDF adapter.** Markitdown handles simple
   PDFs; docling handles tables, multi-column, figures. Pick backend via
   heuristic (file size + a quick layout sniff).
2. **Integration test + benchmark harness.** No live-URL tests exist. Add a
   `tests/fixtures/<adapter>/` directory with golden files and a
   `pytest -m integration` marker for tests that hit real URLs. Use it to
   compare backend quality, latency, and install cost under the same schema.
3. **GitHub repo + CI.** Move out of `sandbox/`, push to GitHub, wire up
   GitHub Actions for `pytest` on push and `python -m build && twine upload`
   on tags.
4. **PyPI alpha release.** `0.1.0a1` to claim the name. Test install from
   TestPyPI before pushing to real PyPI.
5. **More adapters.** Slack export, Notion export, GitHub repo, RSS,
   Gmail mbox. See [docs/adapters.md](docs/adapters.md) §"Adapters worth
   writing".

## Quick start for the next agent

```bash
cd /path/to/docink
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[all,dev]"
pytest -q                            # should print 10 passed
docink --help
```

Try it:

```bash
docink https://example.com           # pulls and renders an article
docink ./some.pdf --json             # full Document as JSON
docink ./paper.pdf --out ./extracted/  # writes <id>.md + <id>.chunks.jsonl
```

## Decisions already made — do not relitigate without reason

These came up during initial scoping. If you want to change one, write
the rationale in your PR.

- **Wrap, don't rebuild.** Every adapter delegates to an existing tool.
  Don't reimplement HTML parsing, PDF parsing, or transcript fetching.
- **Optional extras for backends.** Core has only `pyyaml`. Backends are
  installed via `docink[web]`, `docink[pdf]`, etc. This keeps install size
  small for users who only need one source type.
- **Positional chunk IDs.** Chunks are `c0`, `c1`, ... — not content-hashed.
  The whole-document `content_hash` flags drift; per-chunk identity stays
  stable across small edits.
- **No HTTP client in core.** Each adapter uses its backend's fetch logic.
- **MIT license.** Wrapped backends are all MIT/Apache/Unlicense — no
  copyleft. We can stay MIT. See [docs/licensing.md](docs/licensing.md).
- **One file per adapter.** No base class, no plugin registry, no
  framework. Four files of ~50 lines each is cheaper than one abstraction.

## Open questions / things to discuss with the user

- **Chunking strategies.** Should we add semantic / size-bounded chunking
  behind a `strategy=` parameter, or stay heading-only? User has not
  weighed in.
- **Caching layer.** Currently every extraction fetches fresh. Should we
  add an opt-in disk cache keyed on `canonical_uri`? Probably yes, but
  scope it carefully (TTL? invalidation? location?).
- **Benchmark scoring.** What should count as "best" for each source type:
  human readability, table fidelity, metadata recovery, low boilerplate,
  speed, install size, or cost?
- **GitHub org.** Repo URL is currently a placeholder
  (`github.com/docink/docink`). User needs to claim the org or use their
  personal namespace.

## Where to look for context outside this repo

The user maintains a sandbox of related projects in the same monorepo.
Two are particularly relevant:

- `sandbox/skolpuru/partnership-crm/ground-truth/ground-truth/` — the
  Ground Truth wiki that motivated `docink`. Its `tools/defuddle` script
  and `skills/defuddle-source-capture/SKILL.md` show how the user
  currently uses defuddle as part of an ingest workflow.
- `sandbox/skolpuru/fleet-command-center/fleetio-mcp/` — another MCP
  server the user built. Useful as a reference for MCP server packaging
  conventions and CLI design.

## Communication style

The user prefers:

- Terse responses; no trailing summaries.
- Insight over activity logs.
- Direct disagreement when warranted, not hedging.
- Specific file paths and line numbers in recommendations.

If a change is non-trivial, propose the approach in 2–3 sentences before
implementing.

## What to read next

1. [README.md](README.md) — user-facing pitch.
2. [CLAUDE.md](CLAUDE.md) — project operating rules and pitfalls.
3. [docs/architecture.md](docs/architecture.md) — design rationale.
4. [docs/schema.md](docs/schema.md) — output schema reference.
5. [docs/adapters.md](docs/adapters.md) — adapter contract.
6. [docs/mcp.md](docs/mcp.md) — MCP server usage.
7. [docs/distribution.md](docs/distribution.md) — how users install
   and integrate `docink`.
8. [docs/licensing.md](docs/licensing.md) — license posture and
   wrapped-backend matrix.
9. [CONTRIBUTING.md](CONTRIBUTING.md) — workflow for changes.
10. [CHANGELOG.md](CHANGELOG.md) — what shipped when.
