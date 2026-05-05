from __future__ import annotations

import json
import re
import shutil
import subprocess
from datetime import datetime
from typing import Any
from urllib.parse import parse_qs, unquote, urlparse, urlunparse

import yaml


def extract(uri: str) -> dict[str, Any]:
    """Extract a Readwise Reader document via the official Readwise CLI.

    Supported inputs:
      - readwise://<document-id>
      - reader://<document-id>
      - https://read.readwise.io/<location>/read/<document-id>
      - readwise+https://example.com/article

    The `readwise+https` form saves the URL to Reader first, then fetches the
    resulting Reader document details. It can mutate the user's Reader library.
    """
    target = _parse_target(uri)
    if target["kind"] == "url":
        created = _parse_output(
            _readwise_output("reader-create-document", "--url", target["url"])
        )
        document_id = _document_id_from_payload(created)
        details = _readwise_output(
            "reader-get-document-details",
            "--document-id",
            document_id,
        )
        return _document_payload(details, created_from_url=target["url"])

    details = _readwise_output(
        "reader-get-document-details",
        "--document-id",
        target["document_id"],
    )
    return _document_payload(details)


def _parse_target(uri: str) -> dict[str, str]:
    parsed = urlparse(uri)

    if parsed.scheme in {"readwise+http", "readwise+https"}:
        source_scheme = parsed.scheme.removeprefix("readwise+")
        return {
            "kind": "url",
            "url": urlunparse(
                (
                    source_scheme,
                    parsed.netloc,
                    parsed.path,
                    parsed.params,
                    parsed.query,
                    parsed.fragment,
                )
            ),
        }

    if parsed.scheme in {"readwise", "reader"}:
        query_url = parse_qs(parsed.query).get("url", [None])[0]
        if parsed.netloc == "save" and query_url:
            return {"kind": "url", "url": query_url}
        document_id = (parsed.netloc or parsed.path).strip("/")
        if document_id:
            return {"kind": "document", "document_id": unquote(document_id)}

    if parsed.scheme in {"http", "https"} and _is_reader_host(parsed.netloc):
        document_id = _document_id_from_path(parsed.path)
        if document_id:
            return {"kind": "document", "document_id": document_id}

    raise ValueError(
        "readwise adapter expects readwise://<document-id>, reader://<document-id>, "
        "a Reader document URL, or readwise+https://<url>"
    )


def _is_reader_host(host: str) -> bool:
    host = host.lower()
    return host in {"read.readwise.io", "reader.readwise.io"} or host.endswith(
        ".read.readwise.io"
    )


def _document_id_from_path(path: str) -> str | None:
    parts = [p for p in path.split("/") if p]
    if "read" in parts:
        index = parts.index("read")
        if len(parts) > index + 1:
            return parts[index + 1]
    if parts:
        return parts[-1]
    return None


def _readwise_output(*args: str) -> str:
    if shutil.which("readwise") is None:
        raise RuntimeError(
            "readwise adapter requires the official CLI: "
            "`npm install -g @readwise/cli` then `readwise login`"
        )

    cmd = ["readwise", "--json", *args]
    try:
        completed = subprocess.run(
            cmd,
            check=True,
            capture_output=True,
            text=True,
            timeout=120,
        )
    except subprocess.TimeoutExpired as e:
        raise RuntimeError(f"readwise CLI timed out running {' '.join(cmd)}") from e
    except subprocess.CalledProcessError as e:
        message = (e.stderr or e.stdout or "").strip()
        raise RuntimeError(message or f"readwise CLI failed running {' '.join(cmd)}") from e

    output = completed.stdout.strip()
    if not output:
        raise RuntimeError(f"readwise CLI returned no output running {' '.join(cmd)}")
    return output


def _document_id_from_payload(payload: Any) -> str:
    candidates: list[Any] = []
    if isinstance(payload, dict):
        candidates.extend(
            [
                payload.get("id"),
                payload.get("document_id"),
                payload.get("documentId"),
                payload.get("url"),
            ]
        )
        for key in ("document", "result", "data"):
            nested = payload.get(key)
            if isinstance(nested, dict):
                candidates.extend(
                    [
                        nested.get("id"),
                        nested.get("document_id"),
                        nested.get("documentId"),
                        nested.get("url"),
                    ]
                )

    if isinstance(payload, str):
        candidates.append(payload)

    for candidate in candidates:
        if isinstance(candidate, str) and candidate.strip():
            match = re.search(r"[0-9a-hj-km-np-tv-z]{20,32}", candidate, re.I)
            return match.group(0) if match else candidate.strip()

    raise RuntimeError(f"readwise CLI did not return a document id: {payload!r}")


def _document_payload(output: str, created_from_url: str | None = None) -> dict[str, Any]:
    parsed = _parse_output(output)
    document = _unwrap_document(parsed)
    markdown = _extract_markdown(parsed, document)
    metadata, markdown = _split_frontmatter(markdown)

    if not markdown.strip():
        raise RuntimeError("readwise CLI returned no Markdown content")

    extras = {
        "reader_document_id": _first(document, metadata, "id", "document_id", "documentId"),
        "reader_url": _first(document, metadata, "url"),
        "source_url": _first(document, metadata, "source_url", "sourceUrl"),
        "category": _first(document, metadata, "category"),
        "location": _first(document, metadata, "location"),
        "site_name": _first(document, metadata, "site_name", "siteName"),
        "source": _first(document, metadata, "source"),
        "summary": _first(document, metadata, "summary"),
        "image_url": _first(document, metadata, "image_url", "imageUrl"),
        "word_count": _first(document, metadata, "word_count", "wordCount"),
        "reading_time": _first(document, metadata, "reading_time", "readingTime"),
        "tags": _first(document, metadata, "tags"),
        "notes": _first(document, metadata, "notes"),
        "created_at": _first(document, metadata, "created_at", "createdAt"),
        "updated_at": _first(document, metadata, "updated_at", "updatedAt"),
        "saved_at": _first(document, metadata, "saved_at", "savedAt"),
    }
    if created_from_url:
        extras["created_from_url"] = created_from_url
    extras = {k: v for k, v in extras.items() if v not in (None, "", {}, [])}

    return {
        "markdown": markdown.strip(),
        "title": _nonempty(_first(document, metadata, "title")),
        "author": _nonempty(_first(document, metadata, "author")),
        "published_at": _parse_datetime(
            _first(document, metadata, "published_date", "publishedDate", "published_at")
        ),
        "language": _nonempty(_first(document, metadata, "language")),
        "extractor": f"readwise-cli@{_readwise_version()}",
        "extras": extras,
    }


def _parse_output(output: str) -> Any:
    try:
        return json.loads(output)
    except json.JSONDecodeError:
        return output


def _unwrap_document(parsed: Any) -> dict[str, Any]:
    if not isinstance(parsed, dict):
        return {}
    for key in ("document", "result", "data"):
        value = parsed.get(key)
        if isinstance(value, dict):
            return value
    results = parsed.get("results")
    if isinstance(results, list) and results and isinstance(results[0], dict):
        return results[0]
    return parsed


def _extract_markdown(parsed: Any, document: dict[str, Any]) -> str:
    if isinstance(parsed, str):
        return parsed

    for key in ("markdown", "content", "text", "body"):
        value = document.get(key)
        if isinstance(value, str) and value.strip():
            return value

    content = document.get("content")
    if isinstance(content, list):
        text = "\n".join(
            item.get("text", "") for item in content if isinstance(item, dict)
        ).strip()
        if text:
            return text

    return ""


def _split_frontmatter(markdown: str) -> tuple[dict[str, Any], str]:
    if not markdown.startswith("---\n"):
        return {}, markdown
    end = markdown.find("\n---", 4)
    if end == -1:
        return {}, markdown
    raw_meta = markdown[4:end]
    body = markdown[end + 4 :].lstrip()
    try:
        metadata = yaml.safe_load(raw_meta) or {}
    except yaml.YAMLError:
        return {}, markdown
    if not isinstance(metadata, dict):
        return {}, markdown
    return metadata, body


def _first(document: dict[str, Any], metadata: dict[str, Any], *keys: str) -> Any:
    for source in (document, metadata):
        for key in keys:
            value = source.get(key)
            if value not in (None, ""):
                return value
    return None


def _readwise_version() -> str:
    try:
        completed = subprocess.run(
            ["readwise", "--version"],
            check=True,
            capture_output=True,
            text=True,
            timeout=10,
        )
    except Exception:
        return "unknown"
    return completed.stdout.strip() or "unknown"


def _nonempty(value: Any) -> str | None:
    if value is None:
        return None
    normalized = str(value).strip()
    return normalized or None


def _parse_datetime(value: Any) -> datetime | None:
    if value is None:
        return None
    try:
        return datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError:
        return None
