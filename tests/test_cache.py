from datetime import datetime, timezone

from docink.cache import DocumentCache
from docink.core import Document


def _doc(uri: str, body: str = "# Hi\n\nbody\n") -> Document:
    return Document(
        id="sha256:placeholder",
        canonical_uri=uri,
        source_type="web",
        fetched_at=datetime.now(timezone.utc),
        content_hash="sha256:0",
        markdown=body,
    )


def test_cache_hits_skip_extractor():
    calls: list[str] = []

    def extractor(uri: str) -> Document:
        calls.append(uri)
        return _doc(uri)

    cache = DocumentCache()
    cache.get_or_extract("https://example.com/a", extractor)
    cache.get_or_extract("https://example.com/a", extractor)
    assert calls == ["https://example.com/a"]


def test_cache_canonicalizes_uri():
    calls: list[str] = []

    def extractor(uri: str) -> Document:
        calls.append(uri)
        return _doc(uri)

    cache = DocumentCache()
    cache.get_or_extract("https://example.com/a?utm_source=x", extractor)
    cache.get_or_extract("https://example.com/a", extractor)
    assert len(calls) == 1


def test_cache_ttl_expiry():
    now = [0.0]

    def clock() -> float:
        return now[0]

    def extractor(uri: str) -> Document:
        return _doc(uri)

    cache = DocumentCache(ttl_seconds=10, clock=clock)
    cache.get_or_extract("https://example.com/a", extractor)
    now[0] = 20.0
    extracted_again: list[bool] = []

    def extractor2(uri: str) -> Document:
        extracted_again.append(True)
        return _doc(uri)

    cache.get_or_extract("https://example.com/a", extractor2)
    assert extracted_again == [True]


def test_cache_lru_eviction():
    cache = DocumentCache(max_entries=2)
    cache.get_or_extract("https://example.com/a", lambda u: _doc(u))
    cache.get_or_extract("https://example.com/b", lambda u: _doc(u))
    cache.get_or_extract("https://example.com/c", lambda u: _doc(u))
    assert len(cache) == 2

    refetched: list[str] = []

    def extractor(uri: str) -> Document:
        refetched.append(uri)
        return _doc(uri)

    cache.get_or_extract("https://example.com/a", extractor)
    assert refetched == ["https://example.com/a"]
