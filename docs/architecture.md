# Architecture

## The one-line version

`docink` is a dispatcher, a schema, and a benchmark surface. The actual
extraction is done by existing tools (defuddle, docling, markitdown, yt-dlp).
The value is uniformity and evidence-based backend choice, not owning parser
quality.

## Why this shape

The extraction space is crowded — Firecrawl, Jina Reader, MarkItDown, Docling,
defuddle, trafilatura, readability-lxml, yt-dlp, and a dozen others. Each
one is good at its slice. None of them gives an agent:

1. **A stable identity for a source.** Re-extracting the same URL on Tuesday
   should produce the same document ID it produced on Monday, even if the
   page contents changed slightly.
2. **An addressable cite target.** When an agent says "according to chunk
   c3 of doc sha256:abc...", that string should still resolve a week later.
3. **The same frontmatter shape across heterogeneous sources.** A web page,
   a PDF, and a YouTube video should expose `title`, `author`, `published_at`,
   `language` in the same place.

The cost of building those properties on top of an existing extractor is
small. The benefit to an agent that ingests from many sources is large.
That's the wedge.

The same shape also lets users compare extractors honestly. If defuddle,
trafilatura, docling, and markitdown all return the same `Document` fields,
then benchmarks can focus on practical outcomes: retained body text, lost
tables, boilerplate leakage, metadata recovery, latency, and install cost.

## The three things `docink` owns

### 1. Identity (`ids.py`)

`canonical_uri(uri)` produces a normalized URI by:

- Lowercasing scheme and host.
- Stripping known tracking params (`utm_*`, `fbclid`, `gclid`, etc.).
- Sorting remaining query params alphabetically (so `?a=1&b=2` and `?b=2&a=1`
  hash to the same ID).
- Dropping fragments (`#section`).
- Resolving local file paths to absolute `file://` URIs.

`doc_id(canonical)` is `sha256:` + the first 16 hex chars of the SHA-256 of
the canonical URI. 16 chars (64 bits) is enough collision resistance for any
realistic document corpus.

`content_hash(body)` is the same construction over the markdown body. It's
how an agent detects that the document at a stable `id` has changed.

### 2. Chunking (`chunking.py`)

Default strategy: split at H2 boundaries, with positional IDs (`c0`, `c1`,
...). Each chunk carries its `heading_path` (e.g., `["Article Title",
"Methodology"]`) so an agent has structural context.

Why positional IDs and not content-hashed: small edits in a document
shouldn't reshuffle every chunk's identity. Positional IDs are stable as
long as document *structure* is stable; the document-level `content_hash`
flags when an agent should re-evaluate cached citations.

Future: pluggable strategies (semantic, fixed-token, sliding-window) behind
a `strategy=` parameter. The default stays heading-aware.

### 3. Dispatch (`registry.py`)

URI → source_type detection. Trivial today:

- `youtube.com` / `youtu.be` → `youtube`
- `*.pdf` → `pdf`
- `*.docx`, `*.pptx`, `*.xlsx` → `office`
- Otherwise → `web`

This will get more interesting as adapters proliferate (e.g., `slack-export.zip`
detection, GitHub URL patterns, Notion export structure).

## What `docink` does not own

- **Fetching.** Adapters call their backend's fetch logic directly. There's
  no `docink` HTTP client; if you need caching/retry, layer it outside.
- **Parsing.** All HTML→markdown, PDF→markdown, etc. logic lives in the
  wrapped tool. We don't compete on parser quality; we make quality comparable.
- **Storage.** `docink` returns a `Document`. Where it gets persisted (disk,
  S3, vector DB) is out of scope.
- **Embedding.** Chunks are addressable, but `docink` doesn't compute
  embeddings. That belongs in a downstream indexer.

## Failure modes

The library is designed to fail loudly:

- Missing extras → `RuntimeError` with the exact `pip install` command.
- Adapter can't extract → propagated exception with the source URI.
- Unknown source type → `ValueError` listing supported types.

Fallbacks are explicit in the returned payload. For example, the web adapter
tries defuddle first, then records `extras.fallback_from` and
`extras.backend_attempts` if it has to use trafilatura. An agent should know
when extraction failed or degraded.

## The MCP server

`docink-mcp` exposes the library as an MCP server with two tools:

- `extract(uri) -> dict` — full `Document`.
- `extract_markdown(uri) -> str` — just the markdown-with-frontmatter string.

The point of the MCP layer is that any MCP-capable agent gets URL/file
ingestion for free, without needing to bundle `docink` into the agent itself.

## Roadmap notes

- v0.1 — current scaffold. Web (defuddle with trafilatura fallback), PDF
  (markitdown), YouTube (yt-dlp), Office (markitdown).
- v0.2 — docling for layout-rich PDFs; integration test and benchmark harness
  with golden fixtures per adapter.
- v0.3 — pluggable chunking strategies; Slack/Gmail/Notion exports.
- v1.0 — schema freeze. Once the schema is stable enough to commit to,
  publish a `docink-schema` JSON Schema separately so other tools can
  produce compatible output.
