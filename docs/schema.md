# Output schema reference

This is the contract `docink` exposes to downstream consumers. Once v1.0
ships, this schema will be frozen and breaking changes will require a
major version bump.

## `Document`

The top-level object returned by `extract(uri)`.

| Field | Type | Required | Description |
|---|---|---|---|
| `id` | `str` | yes | `sha256:` + 16 hex chars of `canonical_uri`. Stable across re-extractions of the same URI. |
| `canonical_uri` | `str` | yes | The normalized form of the input URI. Tracking params stripped, query params sorted, fragment dropped. |
| `source_type` | `str` | yes | One of `web`, `pdf`, `youtube`, `office`, `readwise`. New types added as adapters land. |
| `fetched_at` | `datetime` | yes | UTC timestamp of extraction. |
| `content_hash` | `str` | yes | `sha256:` + 16 hex chars of the markdown body. Detects body drift at a stable `id`. |
| `markdown` | `str` | yes | Extracted body. May be empty if extraction returned nothing. |
| `title` | `str \| None` | no | Document title if the extractor surfaced one. |
| `author` | `str \| None` | no | Author or uploader. |
| `published_at` | `datetime \| None` | no | Original publication date if known. |
| `language` | `str \| None` | no | BCP-47 language tag if detected. |
| `extractor` | `str \| None` | no | Name and version of the backend that did the work, e.g., `trafilatura@1.12.0`. |
| `extras` | `dict[str, Any]` | no | Source-type-specific metadata. See per-adapter notes below. |
| `chunks` | `list[Chunk]` | yes | Heading-aware chunks of the markdown body. May be empty. |

## `Chunk`

| Field | Type | Description |
|---|---|---|
| `chunk_id` | `str` | Positional: `c0`, `c1`, .... Stable as long as document structure is stable. |
| `start_line` | `int` | 1-indexed line number where the chunk begins in the markdown body. |
| `end_line` | `int` | 1-indexed line number where the chunk ends (exclusive). |
| `heading_path` | `list[str]` | Heading lineage from H1 down to the chunk's nearest heading. |
| `text` | `str` | The chunk body, including its heading line. |

## Frontmatter form

When serialized via `Document.to_markdown_with_frontmatter()`, the metadata
is rendered as YAML between `---` fences:

```yaml
---
id: sha256:a3f2...
canonical_uri: https://example.com/article
source_type: web
fetched_at: '2026-05-03T12:34:56+00:00'
content_hash: sha256:b7e9...
title: Example Article
author: Jane Doe
published_at: '2025-11-01T00:00:00'
language: en
extractor: trafilatura@1.12.0
---

# Example Article
...
```

Empty optional fields are omitted from the frontmatter rather than emitted
as `null`.

## Sidecar chunks file

When extracted with `--out`, chunks are written to `<id>.chunks.jsonl`,
one JSON object per line:

```json
{"chunk_id": "c0", "start_line": 1, "end_line": 4, "heading_path": ["Example Article"], "text": "# Example Article\n\nIntro paragraph."}
{"chunk_id": "c1", "start_line": 5, "end_line": 12, "heading_path": ["Example Article", "Background"], "text": "## Background\n\n..."}
```

JSONL because chunks are independently consumable — an indexer can stream the
file without materializing the whole document in memory.

## Per-adapter `extras`

The `extras` dict is freeform but each adapter has a documented shape.

### `web` extras

Currently empty. Planned: `canonical_url` (from `<link rel=canonical>` if
different from input URI), `og_image`, `word_count`.

### `pdf` extras

Currently empty. Planned: `page_count`, `has_tables`, `has_images`.

### `youtube` extras

| Key | Type | Description |
|---|---|---|
| `video_id` | `str` | YouTube video ID. |
| `duration_seconds` | `int` | Total runtime. |
| `channel` | `str` | Channel name. |

### `office` extras

Currently empty. Planned: `page_count` (docx/pptx), `sheet_count` (xlsx).

### `readwise` extras

| Key | Type | Description |
|---|---|---|
| `reader_document_id` | `str` | Reader document ID, when surfaced by the CLI. |
| `reader_url` | `str` | Reader app URL for the saved document. |
| `source_url` | `str` | Original source URL, when known. |
| `category` | `str` | Reader category such as `article`, `pdf`, `video`, or `podcast`. |
| `location` | `str` | Reader location such as `new`, `later`, `shortlist`, `archive`, or `feed`. |
| `site_name` | `str` | Site/source name from Reader metadata. |
| `word_count` | `int` | Reader's word count. |
| `reading_time` | `str` | Reader's estimated reading time. |
| `summary` | `str` | Reader summary, when available. |
| `tags` | `dict \| list` | Reader tags as returned by the CLI. |
| `created_from_url` | `str` | Present only for `readwise+https://...`; the URL docink asked Reader to save. |

## Stability guarantees

- **Pre-1.0:** schema may change in minor versions. Watch the changelog.
- **1.0 onward:** field additions are non-breaking. Field removals or
  type changes require a major version bump. The `extras` dict is the
  release valve for adapter-specific data that doesn't merit a top-level
  field.
