# Attributions

`docink` stands on the shoulders of these open-source projects. Each is
declared as an optional dependency and installed from its authoritative
distribution channel; we don't vendor or redistribute their source.

## Wrapped extractors

### [trafilatura](https://github.com/adbar/trafilatura)
- **License:** Apache 2.0
- **Used by:** `docink.adapters.web`
- **What it does:** HTML article extraction with metadata recovery.
- **Why we use it:** Solid pure-Python fallback; ships on PyPI.

### [defuddle](https://github.com/kepano/defuddle)
- **License:** MIT (npm)
- **Used by:** `docink.adapters.web`
- **What it does:** Browser-grade content extraction with strong boilerplate
  removal.
- **Why we use it:** Best-in-class web extraction, including YouTube
  transcripts.

### [markitdown](https://github.com/microsoft/markitdown)
- **License:** MIT
- **Used by:** `docink.adapters.pdf`, `docink.adapters.office`
- **What it does:** Converts a wide range of document formats to markdown.
- **Why we use it:** One library covers PDF + docx + pptx + xlsx with
  reasonable quality.

### [docling](https://github.com/DS4SD/docling) (planned)
- **License:** MIT
- **Used by:** `docink.adapters.pdf` (planned for layout-rich PDFs)
- **What it does:** Document parsing with structural awareness — tables,
  multi-column, figures.
- **Why we use it:** Better than markitdown for complex PDFs; we'll pick
  via heuristic.

### [yt-dlp](https://github.com/yt-dlp/yt-dlp)
- **License:** Unlicense (public domain)
- **Used by:** `docink.adapters.youtube`
- **What it does:** Pulls metadata and subtitles from YouTube and many
  other video platforms.
- **Why we use it:** Robust, actively maintained, handles edge cases that
  break other extractors.

## External services and CLIs

### [Readwise CLI](https://github.com/readwiseio/readwise-cli)
- **License:** No license declared in the npm package at time of integration.
- **Used by:** `docink.adapters.readwise`
- **What it does:** Authenticated access to Readwise and Reader documents.
- **Why we use it:** The official CLI exposes Reader document details as
  Markdown. `docink` shells out to a user-installed CLI and does not vendor
  or redistribute it.

## Other dependencies

### [fastmcp](https://github.com/jlowin/fastmcp)
- **License:** Apache 2.0
- **Used by:** `docink.mcp.server`
- **What it does:** MCP server framework.

### [pyyaml](https://pyyaml.org)
- **License:** MIT
- **Used by:** core (`Document.to_markdown_with_frontmatter`)

## How to add a new attribution

When you add a new adapter that wraps a third-party tool:

1. Add an entry above with the project name, repo URL, license, and a
   one-line description.
2. Add the project to the license matrix in [docs/licensing.md](docs/licensing.md).
3. Confirm the license is permissive (MIT / Apache 2.0 / BSD / ISC /
   Unlicense). If it's GPL/AGPL/LGPL, see the special-case guidance in
   [docs/licensing.md](docs/licensing.md).
