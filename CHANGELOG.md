# Changelog

All notable changes to `docink` are documented here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and the project
follows [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Initial v0.1 scaffolding: `Document` / `Chunk` schema, deterministic IDs,
  heading-aware chunker, CLI, MCP server skeleton.
- `web` adapter via defuddle with trafilatura fallback.
- `pdf` adapter via markitdown.
- `youtube` adapter via yt-dlp with `[hh:mm:ss]` anchors.
- `office` adapter (docx/pptx/xlsx) via markitdown.
- Experimental `readwise` adapter via the official Readwise CLI.
- Unit tests for ID canonicalization and chunking.

### Known gaps
- docling backend deferred (PDF adapter is markitdown-only).
- No integration tests with golden fixtures yet.
- `published_at` parsing is naive (ISO only).
