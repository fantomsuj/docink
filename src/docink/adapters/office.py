from __future__ import annotations

from pathlib import Path
from typing import Any
from urllib.parse import urlparse


def extract(uri: str) -> dict[str, Any]:
    """Extract docx/pptx/xlsx to markdown via markitdown."""
    try:
        from markitdown import MarkItDown
    except ImportError as e:
        raise RuntimeError(
            "office adapter requires `pip install docink[office]` (markitdown)"
        ) from e

    parsed = urlparse(uri)
    if parsed.scheme in ("http", "https"):
        source: str | Path = uri
    else:
        source = Path(parsed.path if parsed.scheme == "file" else uri).expanduser().resolve()
        if not source.exists():
            raise FileNotFoundError(source)

    md = MarkItDown()
    result = md.convert(str(source))

    return {
        "markdown": result.text_content or "",
        "title": getattr(result, "title", None),
        "author": None,
        "published_at": None,
        "language": None,
        "extractor": "markitdown",
        "extras": {},
    }
