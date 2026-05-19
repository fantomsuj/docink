from datetime import datetime, timezone

import pytest

from docink.cache import DocumentCache
from docink.chunking import chunk_by_headings
from docink.core import Chunk, Document
from docink.mcp import tools as mcp_tools

_MD = (
    "# Quarterly Report\n\n"
    "Intro paragraph mentioning revenue once.\n\n"
    "## Revenue\n\n"
    "Revenue grew. Revenue revenue revenue. Total revenue jumped.\n\n"
    "## Costs\n\n"
    "Costs were stable this quarter.\n\n"
    "## Outlook\n\n"
    "Next quarter we expect more revenue and lower costs.\n"
)


def _fake_extractor(uri: str) -> Document:
    raw = chunk_by_headings(_MD)
    return Document(
        id="sha256:fake",
        canonical_uri=uri,
        source_type="web",
        fetched_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
        content_hash="sha256:0",
        markdown=_MD,
        title="Quarterly Report",
        chunks=[Chunk(**c) for c in raw],
    )


def test_list_chunks_returns_index_without_full_text():
    cache = DocumentCache()
    result = mcp_tools.list_chunks(
        "https://example.com/r", cache=cache, extractor=_fake_extractor
    )
    assert result["chunk_count"] == 4
    assert [c["chunk_id"] for c in result["chunks"]] == ["c0", "c1", "c2", "c3"]
    for c in result["chunks"]:
        assert "preview" in c
        assert len(c["preview"]) <= 120
        assert "text" not in c


def test_get_chunk_returns_full_text():
    cache = DocumentCache()
    result = mcp_tools.get_chunk(
        "https://example.com/r", "c1", cache=cache, extractor=_fake_extractor
    )
    assert result["chunk_id"] == "c1"
    assert "Revenue grew" in result["text"]
    assert result["heading_path"] == ["Quarterly Report", "Revenue"]


def test_get_chunk_unknown_id_raises_with_available_ids():
    cache = DocumentCache()
    with pytest.raises(ValueError, match=r"c0"):
        mcp_tools.get_chunk(
            "https://example.com/r", "c99", cache=cache, extractor=_fake_extractor
        )


def test_search_chunks_ranks_by_term_frequency():
    cache = DocumentCache()
    result = mcp_tools.search_chunks(
        "https://example.com/r",
        "revenue",
        cache=cache,
        extractor=_fake_extractor,
    )
    assert result["results"][0]["chunk_id"] == "c1"
    assert result["results"][0]["score"] >= result["results"][1]["score"]
    assert "revenue" in result["results"][0]["snippet"].lower()


def test_search_chunks_heading_boost():
    cache = DocumentCache()
    result = mcp_tools.search_chunks(
        "https://example.com/r",
        "Outlook",
        cache=cache,
        extractor=_fake_extractor,
    )
    assert result["results"][0]["chunk_id"] == "c3"


def test_search_chunks_empty_query_raises():
    cache = DocumentCache()
    with pytest.raises(ValueError):
        mcp_tools.search_chunks(
            "https://example.com/r", "   ", cache=cache, extractor=_fake_extractor
        )


def test_tools_share_cache_across_calls():
    calls: list[str] = []

    def counting_extractor(uri: str) -> Document:
        calls.append(uri)
        return _fake_extractor(uri)

    cache = DocumentCache()
    mcp_tools.list_chunks("https://example.com/r", cache=cache, extractor=counting_extractor)
    mcp_tools.get_chunk(
        "https://example.com/r", "c0", cache=cache, extractor=counting_extractor
    )
    mcp_tools.search_chunks(
        "https://example.com/r", "revenue", cache=cache, extractor=counting_extractor
    )
    assert len(calls) == 1
