from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

import yaml

from docink import ids as _ids
from docink.chunking import chunk_by_headings
from docink.registry import detect_source_type, get_adapter


@dataclass
class Chunk:
    chunk_id: str
    start_line: int
    end_line: int
    heading_path: list[str]
    text: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "chunk_id": self.chunk_id,
            "start_line": self.start_line,
            "end_line": self.end_line,
            "heading_path": self.heading_path,
            "text": self.text,
        }


@dataclass
class Document:
    id: str
    canonical_uri: str
    source_type: str
    fetched_at: datetime
    content_hash: str
    markdown: str = ""
    title: str | None = None
    author: str | None = None
    published_at: datetime | None = None
    language: str | None = None
    extractor: str | None = None
    extras: dict[str, Any] = field(default_factory=dict)
    chunks: list[Chunk] = field(default_factory=list)

    @property
    def metadata(self) -> dict[str, Any]:
        meta: dict[str, Any] = {
            "id": self.id,
            "canonical_uri": self.canonical_uri,
            "source_type": self.source_type,
            "fetched_at": self.fetched_at.isoformat(),
            "content_hash": self.content_hash,
        }
        if self.title is not None:
            meta["title"] = self.title
        if self.author is not None:
            meta["author"] = self.author
        if self.published_at is not None:
            meta["published_at"] = self.published_at.isoformat()
        if self.language is not None:
            meta["language"] = self.language
        if self.extractor is not None:
            meta["extractor"] = self.extractor
        if self.extras:
            meta["extras"] = self.extras
        return meta

    def to_dict(self) -> dict[str, Any]:
        return {
            **self.metadata,
            "markdown": self.markdown,
            "chunks": [c.to_dict() for c in self.chunks],
        }

    def to_markdown_with_frontmatter(self) -> str:
        front = yaml.safe_dump(self.metadata, sort_keys=False, allow_unicode=True).strip()
        return f"---\n{front}\n---\n\n{self.markdown}".rstrip() + "\n"


def extract(uri: str) -> Document:
    """Top-level entry point: dispatch `uri` to the right adapter and assemble a Document."""
    source_type = detect_source_type(uri)
    adapter = get_adapter(source_type)
    if adapter is None:
        raise ValueError(
            f"No adapter for source_type={source_type!r} (uri={uri!r}). "
            "Available: web, pdf, youtube, office, readwise."
        )

    canonical = _ids.canonical_uri(uri)
    payload = adapter.extract(uri)

    markdown: str = payload.get("markdown", "")
    raw_chunks = chunk_by_headings(markdown) if markdown else []
    chunks = [Chunk(**c) for c in raw_chunks]

    return Document(
        id=_ids.doc_id(canonical),
        canonical_uri=canonical,
        source_type=source_type,
        fetched_at=datetime.now(timezone.utc),
        content_hash=_ids.content_hash(markdown),
        markdown=markdown,
        title=payload.get("title"),
        author=payload.get("author"),
        published_at=payload.get("published_at"),
        language=payload.get("language"),
        extractor=payload.get("extractor"),
        extras=payload.get("extras", {}),
        chunks=chunks,
    )
