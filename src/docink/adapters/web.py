from __future__ import annotations

from datetime import datetime
from typing import Any


def extract(uri: str) -> dict[str, Any]:
    """Extract a web page to markdown.

    Backend strategy:
        1. defuddle (via local node binary or `npx defuddle`) — primary, best at boilerplate removal.
        2. trafilatura — pure-Python fallback when defuddle unavailable or fails.

    Returns a dict with keys: markdown, title, author, published_at, language, extractor, extras.
    """
    try:
        import trafilatura
    except ImportError as e:
        raise RuntimeError(
            "web adapter requires `pip install docink[web]` (trafilatura)"
        ) from e

    downloaded = trafilatura.fetch_url(uri)
    if downloaded is None:
        raise RuntimeError(f"Failed to fetch {uri}")

    markdown = trafilatura.extract(
        downloaded,
        output_format="markdown",
        include_links=True,
        include_images=True,
        with_metadata=False,
    )
    if not markdown:
        raise RuntimeError(f"trafilatura extracted no content from {uri}")

    metadata = trafilatura.extract_metadata(downloaded)
    title = getattr(metadata, "title", None) if metadata else None
    author = getattr(metadata, "author", None) if metadata else None
    date_str = getattr(metadata, "date", None) if metadata else None
    language = getattr(metadata, "language", None) if metadata else None

    published_at: datetime | None = None
    if date_str:
        try:
            published_at = datetime.fromisoformat(date_str)
        except ValueError:
            published_at = None

    return {
        "markdown": markdown,
        "title": title,
        "author": author,
        "published_at": published_at,
        "language": language,
        "extractor": f"trafilatura@{trafilatura.__version__}",
        "extras": {},
    }
