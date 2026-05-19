from __future__ import annotations

import re
from typing import Any, Callable

from docink.cache import DocumentCache
from docink.core import Chunk, Document, extract as _extract

_PREVIEW_CHARS = 120
_SNIPPET_RADIUS = 80
_DEFAULT_SEARCH_LIMIT = 5
_HEADING_BOOST = 3


def make_cache() -> DocumentCache:
    return DocumentCache()


def list_chunks(
    uri: str,
    *,
    cache: DocumentCache,
    extractor: Callable[[str], Document] = _extract,
) -> dict[str, Any]:
    doc = cache.get_or_extract(uri, extractor)
    return {
        "doc_id": doc.id,
        "canonical_uri": doc.canonical_uri,
        "source_type": doc.source_type,
        "title": doc.title,
        "content_hash": doc.content_hash,
        "chunk_count": len(doc.chunks),
        "chunks": [_chunk_summary(c) for c in doc.chunks],
    }


def get_chunk(
    uri: str,
    chunk_id: str,
    *,
    cache: DocumentCache,
    extractor: Callable[[str], Document] = _extract,
) -> dict[str, Any]:
    doc = cache.get_or_extract(uri, extractor)
    for c in doc.chunks:
        if c.chunk_id == chunk_id:
            return {
                "doc_id": doc.id,
                "canonical_uri": doc.canonical_uri,
                **c.to_dict(),
            }
    available = [c.chunk_id for c in doc.chunks]
    raise ValueError(
        f"No chunk {chunk_id!r} in {doc.id} ({len(available)} chunks: "
        f"{', '.join(available[:8])}{'...' if len(available) > 8 else ''})"
    )


def search_chunks(
    uri: str,
    query: str,
    *,
    limit: int = _DEFAULT_SEARCH_LIMIT,
    cache: DocumentCache,
    extractor: Callable[[str], Document] = _extract,
) -> dict[str, Any]:
    if not query.strip():
        raise ValueError("search_chunks: query is empty")
    doc = cache.get_or_extract(uri, extractor)
    scored = _rank(doc.chunks, query)
    return {
        "doc_id": doc.id,
        "canonical_uri": doc.canonical_uri,
        "query": query,
        "result_count": len(scored),
        "results": [
            {
                "chunk_id": c.chunk_id,
                "heading_path": c.heading_path,
                "score": score,
                "snippet": _snippet(c.text, query),
                "start_line": c.start_line,
                "end_line": c.end_line,
            }
            for c, score in scored[: max(1, limit)]
        ],
    }


def _chunk_summary(c: Chunk) -> dict[str, Any]:
    preview = re.sub(r"\s+", " ", c.text).strip()[:_PREVIEW_CHARS]
    return {
        "chunk_id": c.chunk_id,
        "heading_path": c.heading_path,
        "start_line": c.start_line,
        "end_line": c.end_line,
        "char_count": len(c.text),
        "preview": preview,
    }


def _rank(chunks: list[Chunk], query: str) -> list[tuple[Chunk, int]]:
    terms = [t for t in re.split(r"\s+", query.lower()) if t]
    if not terms:
        return []
    scored: list[tuple[Chunk, int]] = []
    for c in chunks:
        text_lc = c.text.lower()
        heading_lc = " / ".join(c.heading_path).lower()
        score = 0
        for term in terms:
            score += text_lc.count(term)
            score += heading_lc.count(term) * _HEADING_BOOST
        if score > 0:
            scored.append((c, score))
    scored.sort(key=lambda pair: (-pair[1], pair[0].start_line))
    return scored


def _snippet(text: str, query: str) -> str:
    terms = [t for t in re.split(r"\s+", query.lower()) if t]
    text_lc = text.lower()
    best = -1
    for term in terms:
        idx = text_lc.find(term)
        if idx != -1 and (best == -1 or idx < best):
            best = idx
    if best == -1:
        return re.sub(r"\s+", " ", text[: 2 * _SNIPPET_RADIUS]).strip()
    start = max(0, best - _SNIPPET_RADIUS)
    end = min(len(text), best + _SNIPPET_RADIUS)
    snip = re.sub(r"\s+", " ", text[start:end]).strip()
    prefix = "..." if start > 0 else ""
    suffix = "..." if end < len(text) else ""
    return f"{prefix}{snip}{suffix}"
