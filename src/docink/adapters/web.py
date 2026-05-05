from __future__ import annotations

import json
import os
import shutil
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Any
from urllib.parse import unquote, urlparse

DEFUDDLE_PACKAGE = "defuddle@0.14.0"


def extract(uri: str) -> dict[str, Any]:
    """Extract a web page to markdown.

    Backend strategy:
        1. defuddle (via local node binary or `npx defuddle`) — primary, best at boilerplate removal.
        2. trafilatura — pure-Python fallback when defuddle unavailable or fails.

    Returns a dict with keys: markdown, title, author, published_at, language, extractor, extras.
    """
    attempts: list[dict[str, str]] = []

    try:
        return _extract_defuddle(uri)
    except Exception as e:
        attempts.append({"extractor": "defuddle", "error": str(e)})

    try:
        result = _extract_trafilatura(uri)
    except Exception as e:
        raise RuntimeError(
            "web extraction failed; "
            f"defuddle: {attempts[0]['error']}; trafilatura: {e}"
        ) from e

    result["extras"] = {
        **result.get("extras", {}),
        "fallback_from": "defuddle",
        "backend_attempts": attempts,
    }
    return result


def extract_with_backend(uri: str, backend: str = "auto") -> dict[str, Any]:
    """Extract with a specific web backend.

    `backend="auto"` matches `extract()`. Use explicit backends for benchmarks.
    """
    if backend == "auto":
        return extract(uri)
    if backend == "defuddle":
        return _extract_defuddle(uri)
    if backend == "trafilatura":
        return _extract_trafilatura(uri)
    raise ValueError("backend must be one of: auto, defuddle, trafilatura")


def _extract_defuddle(uri: str) -> dict[str, Any]:
    cmd = [
        *_defuddle_command(),
        "parse",
        "--json",
        "--markdown",
        _defuddle_source(uri),
    ]
    try:
        completed = subprocess.run(
            cmd,
            check=True,
            capture_output=True,
            text=True,
            timeout=60,
        )
    except FileNotFoundError as e:
        raise RuntimeError(
            "defuddle requires Node.js with `npx`, or set DEFUDDLE_BIN"
        ) from e
    except subprocess.TimeoutExpired as e:
        raise RuntimeError(f"defuddle timed out extracting {uri}") from e
    except subprocess.CalledProcessError as e:
        message = (e.stderr or e.stdout or "").strip()
        raise RuntimeError(message or f"defuddle failed extracting {uri}") from e

    try:
        payload = json.loads(completed.stdout)
    except json.JSONDecodeError as e:
        raise RuntimeError("defuddle returned invalid JSON") from e

    markdown = str(payload.get("content") or "").strip()
    if not markdown:
        raise RuntimeError(f"defuddle extracted no content from {uri}")

    return {
        "markdown": markdown,
        "title": _nonempty(payload.get("title")),
        "author": _nonempty(payload.get("author")),
        "published_at": _parse_datetime(_nonempty(payload.get("published"))),
        "language": _nonempty(payload.get("language")),
        "extractor": f"defuddle@{_defuddle_version()}",
        "extras": {
            "description": _nonempty(payload.get("description")),
            "domain": _nonempty(payload.get("domain")),
            "site": _nonempty(payload.get("site")),
            "word_count": payload.get("wordCount"),
            "parse_time_ms": payload.get("parseTime"),
        },
    }


def _defuddle_command() -> list[str]:
    if os.environ.get("DEFUDDLE_BIN"):
        return [os.environ["DEFUDDLE_BIN"]]
    for root in (Path.cwd(), Path(__file__).resolve().parents[3]):
        local_bin = root / "node_modules" / ".bin" / "defuddle"
        if local_bin.is_file() and os.access(local_bin, os.X_OK):
            return [str(local_bin)]
    if shutil.which("defuddle"):
        return ["defuddle"]
    return ["npx", "--yes", DEFUDDLE_PACKAGE]


def _defuddle_source(uri: str) -> str:
    parsed = urlparse(uri)
    if parsed.scheme == "file":
        return unquote(parsed.path)
    return uri


def _defuddle_version() -> str:
    if "@" in DEFUDDLE_PACKAGE:
        return DEFUDDLE_PACKAGE.rsplit("@", 1)[1]
    return "unknown"


def _extract_trafilatura(uri: str) -> dict[str, Any]:
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

    return {
        "markdown": markdown,
        "title": _nonempty(title),
        "author": _nonempty(author),
        "published_at": _parse_datetime(_nonempty(date_str)),
        "language": _nonempty(language),
        "extractor": f"trafilatura@{trafilatura.__version__}",
        "extras": {},
    }


def _nonempty(value: Any) -> str | None:
    if value is None:
        return None
    normalized = str(value).strip()
    return normalized or None


def _parse_datetime(value: str | None) -> datetime | None:
    if value is None:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
