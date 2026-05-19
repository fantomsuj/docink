from __future__ import annotations


def main() -> int:
    try:
        from fastmcp import FastMCP
    except ImportError:
        print(
            "docink-mcp requires `pip install docink[mcp]` (fastmcp)",
            flush=True,
        )
        return 2

    from docink.core import extract as _extract
    from docink.mcp import tools as _tools

    mcp = FastMCP("docink")
    cache = _tools.make_cache()

    @mcp.tool()
    def extract(uri: str) -> dict:
        """Extract any URL or file path to agent-readable markdown with stable IDs.

        Supported sources: web pages, PDFs, YouTube videos, Office docs
        (docx/pptx/xlsx), and Readwise Reader documents.
        Returns the full Document including markdown body, frontmatter metadata, and
        addressable chunks. For long documents, prefer `list_chunks` + `get_chunk`
        to avoid pulling the whole body into context.
        """
        doc = cache.get_or_extract(uri, _extract)
        return doc.to_dict()

    @mcp.tool()
    def extract_markdown(uri: str) -> str:
        """Extract any URL or file path to a markdown string with YAML frontmatter."""
        doc = cache.get_or_extract(uri, _extract)
        return doc.to_markdown_with_frontmatter()

    @mcp.tool()
    def list_chunks(uri: str) -> dict:
        """Index a document's chunks without returning full text.

        Returns `doc_id`, `chunk_count`, and one entry per chunk with
        `chunk_id`, `heading_path`, line range, char count, and a short
        preview. Cheap follow-up to call `get_chunk` against.
        """
        return _tools.list_chunks(uri, cache=cache, extractor=_extract)

    @mcp.tool()
    def get_chunk(uri: str, chunk_id: str) -> dict:
        """Return one addressable chunk by its `chunk_id` (e.g. `c3`).

        Pair with `list_chunks` to discover available chunk IDs. Re-uses
        the cached extraction if the URI was fetched recently.
        """
        return _tools.get_chunk(uri, chunk_id, cache=cache, extractor=_extract)

    @mcp.tool()
    def search_chunks(uri: str, query: str, limit: int = 5) -> dict:
        """Rank chunks by occurrences of `query` terms, return top `limit` with snippets.

        Case-insensitive substring match across each chunk's text and heading
        path (heading hits weighted higher). Use for "where in this doc is X"
        questions before pulling full chunk text via `get_chunk`.
        """
        return _tools.search_chunks(
            uri, query, limit=limit, cache=cache, extractor=_extract
        )

    mcp.run()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
