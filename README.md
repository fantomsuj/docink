# docink

Agent-readable extraction of any source into markdown — with stable IDs, provenance, and chunk addresses that survive re-extraction.

`docink` is not another HTML-to-markdown converter. It's a thin, opinionated layer over the best existing extractors (defuddle, docling, markitdown, yt-dlp), unified behind one schema that agents can rely on and benchmark.

## Why

Existing tools (Firecrawl, MarkItDown, Docling, defuddle, trafilatura) each do one thing well. None of them give an agent:

- **Stable document IDs** — same URI in, same `id` out, always.
- **Addressable chunks** — `{doc_id}#{chunk_id}` survives re-extraction, with `content_hash` flagging drift.
- **Uniform frontmatter** — title, author, fetched_at, source_type, extractor, language across all sources.
- **Source-type dispatch** — one entry point for web, PDF, YouTube, Office docs.

That uniformity is the product. The extractors underneath are interchangeable.
It also makes extractor quality comparable: run multiple backends against the
same source corpus, inspect the same schema, and choose the backend that fits
your use case instead of guessing from one-off demos.

## Install

```bash
pip install docink                  # core only
pip install docink[web]             # + trafilatura; defuddle runs through Node/npx
pip install docink[pdf]             # + docling, markitdown
pip install docink[youtube]         # + yt-dlp
pip install docink[office]          # + markitdown
pip install docink[all]             # everything
pip install docink[mcp]             # + fastmcp for the MCP server
npm install -g @readwise/cli        # optional: Readwise Reader adapter
readwise login                      # optional: authenticate Readwise CLI
```

## CLI

```bash
docink https://example.com/article             # markdown to stdout
docink https://example.com/article --json      # full Document as JSON
docink ./paper.pdf --out ./extracted/          # write {id}.md + {id}.chunks.jsonl
docink "https://youtu.be/VIDEO_ID"             # transcript with [hh:mm:ss] anchors
docink "readwise://READER_DOCUMENT_ID"         # saved Reader doc via Readwise CLI
docink "readwise+https://example.com/article"  # save to Reader, then extract
```

## Library

```python
from docink import extract

doc = extract("https://example.com/article")
doc.markdown            # str
doc.metadata            # dict (frontmatter)
doc.chunks              # list[Chunk] with stable chunk_ids
doc.to_markdown_with_frontmatter()
```

## MCP server

```bash
docink-mcp                          # stdio MCP server
```

Exposes five tools so agents can both pull a whole document and drill into it cheaply:

- `extract(uri) → Document` — full document with markdown, metadata, chunks.
- `extract_markdown(uri) → str` — markdown with YAML frontmatter only.
- `list_chunks(uri) → dict` — chunk index (IDs, heading paths, previews) without full text.
- `get_chunk(uri, chunk_id) → dict` — one addressable chunk by its `chunk_id` (e.g. `c3`).
- `search_chunks(uri, query, limit=5) → dict` — rank chunks by query term frequency, with snippets.

Drop into Claude Desktop / Cursor / Cline config and any agent gets URL-and-file ingestion for free. The server caches extractions in-process, so a `list_chunks` → `get_chunk` flow only fetches once.

## Output schema

```yaml
---
id: sha256:a3f2...                # deterministic from canonical_uri
canonical_uri: https://example.com/article
source_type: web                  # web | pdf | youtube | office | ...
fetched_at: 2026-05-03T12:34:56Z
content_hash: sha256:...          # of the markdown body
title: Example Article
author: Jane Doe
published_at: 2025-11-01
language: en
extractor: defuddle@0.14.0        # which tool actually did the work
extras: {}                        # source-type-specific
---

# Example Article
...
```

Sidecar `<id>.chunks.jsonl` (one chunk per line):

```json
{"chunk_id": "c0", "start_line": 1, "end_line": 12, "heading_path": ["Example Article"], "text": "..."}
```

## Adapters (v0.1)

| Source | Adapter | Backend |
|--------|---------|---------|
| Web pages | `web` | defuddle, trafilatura fallback |
| PDFs | `pdf` | docling (rich) or markitdown (fast) |
| YouTube | `youtube` | yt-dlp transcript + chapters |
| Office docs | `office` | markitdown (docx/pptx/xlsx) |
| Readwise Reader | `readwise` | official Readwise CLI |

Planned for v0.2: Slack export, Gmail, Drive, Notion, GitHub repos.

## Design invariants

1. **Idempotent** — `extract(uri)` is pure-ish. Re-running with the same URI returns the same `id`. Body changes are caught via `content_hash`.
2. **Addressable** — every chunk has a stable `chunk_id` so an agent's citation `{doc_id}#{chunk_id}` is durable.
3. **Wrap, don't rebuild** — adapters delegate to existing extractors. `docink` owns the schema, dispatch, and ID strategy. Nothing else.

## Documentation

- [docs/architecture.md](docs/architecture.md) — design rationale and what the library does (and does not) own.
- [docs/schema.md](docs/schema.md) — full output schema reference.
- [docs/adapters.md](docs/adapters.md) — adapter contract; how to add a new source type.
- [docs/mcp.md](docs/mcp.md) — MCP server usage with client-by-client config.
- [docs/distribution.md](docs/distribution.md) — packaging and how end users install across PyPI / GitHub / MCPB.
- [docs/licensing.md](docs/licensing.md) — license posture, wrapped-backend matrix, OSS-wrapping best practices.
- [AGENTS.md](AGENTS.md) — handoff context for autonomous coding agents picking up this repo.
- [CLAUDE.md](CLAUDE.md) — project operating rules and pitfalls.
- [CONTRIBUTING.md](CONTRIBUTING.md) — workflow for changes.
- [CHANGELOG.md](CHANGELOG.md) — what shipped when.
- [ATTRIBUTIONS.md](ATTRIBUTIONS.md) — credit for the projects we wrap.

## License

`docink` is MIT-licensed. The backends it wraps (trafilatura, markitdown, yt-dlp, docling, fastmcp, pyyaml, and defuddle) are all permissively licensed (MIT / Apache 2.0 / Unlicense). See [docs/licensing.md](docs/licensing.md) and [ATTRIBUTIONS.md](ATTRIBUTIONS.md) for the full picture.
