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

    mcp = FastMCP("docink")

    @mcp.tool()
    def extract(uri: str) -> dict:
        """Extract any URL or file path to agent-readable markdown with stable IDs.

        Supported sources: web pages, PDFs, YouTube videos, Office docs
        (docx/pptx/xlsx), and Readwise Reader documents.
        Returns the full Document including markdown body, frontmatter metadata, and
        addressable chunks.
        """
        doc = _extract(uri)
        return doc.to_dict()

    @mcp.tool()
    def extract_markdown(uri: str) -> str:
        """Extract any URL or file path to a markdown string with YAML frontmatter."""
        doc = _extract(uri)
        return doc.to_markdown_with_frontmatter()

    mcp.run()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
