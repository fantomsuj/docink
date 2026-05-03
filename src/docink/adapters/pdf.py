from __future__ import annotations

from pathlib import Path
from typing import Any
from urllib.parse import urlparse


def extract(uri: str) -> dict[str, Any]:
    """Extract a PDF to markdown via markitdown.

    For layout-rich PDFs (tables, multi-column), a future docling backend will
    produce better results; markitdown is the fast default.
    """
    try:
        from markitdown import MarkItDown
    except ImportError as e:
        raise RuntimeError(
            "pdf adapter requires `pip install docink[pdf]` (markitdown)"
        ) from e

    parsed = urlparse(uri)
    source: str | Path
    if parsed.scheme in ("http", "https"):
        source = uri
    else:
        source = Path(parsed.path if parsed.scheme == "file" else uri).expanduser().resolve()
        if not source.exists():
            raise FileNotFoundError(source)

    md = MarkItDown()
    result = md.convert(str(source))
    markdown = result.text_content or ""

    return {
        "markdown": markdown,
        "title": getattr(result, "title", None),
        "author": None,
        "published_at": None,
        "language": None,
        "extractor": "markitdown",
        "extras": {},
    }
