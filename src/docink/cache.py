from __future__ import annotations

import time
from collections import OrderedDict
from typing import Callable

from docink import ids as _ids
from docink.core import Document

_DEFAULT_TTL_SECONDS = 3600
_DEFAULT_MAX_ENTRIES = 32


class DocumentCache:
    """In-process LRU+TTL cache of extracted Documents, keyed by `doc_id`.

    Extraction is the expensive step (network fetch, subprocess, parsing).
    Agents typically call `list_chunks`, then `get_chunk`/`search_chunks`
    against the same URI in quick succession — re-extracting each time
    would defeat the addressable-chunk design.
    """

    def __init__(
        self,
        max_entries: int = _DEFAULT_MAX_ENTRIES,
        ttl_seconds: int = _DEFAULT_TTL_SECONDS,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        self._entries: OrderedDict[str, tuple[Document, float]] = OrderedDict()
        self._max = max_entries
        self._ttl = ttl_seconds
        self._clock = clock

    def get_or_extract(
        self,
        uri: str,
        extractor: Callable[[str], Document],
    ) -> Document:
        key = _ids.doc_id(_ids.canonical_uri(uri))
        now = self._clock()

        hit = self._entries.get(key)
        if hit is not None:
            doc, ts = hit
            if now - ts <= self._ttl:
                self._entries.move_to_end(key)
                return doc
            del self._entries[key]

        doc = extractor(uri)
        self._entries[key] = (doc, now)
        self._entries.move_to_end(key)
        while len(self._entries) > self._max:
            self._entries.popitem(last=False)
        return doc

    def peek_by_id(self, doc_id: str) -> Document | None:
        hit = self._entries.get(doc_id)
        if hit is None:
            return None
        doc, ts = hit
        if self._clock() - ts > self._ttl:
            del self._entries[doc_id]
            return None
        self._entries.move_to_end(doc_id)
        return doc

    def clear(self) -> None:
        self._entries.clear()

    def __len__(self) -> int:
        return len(self._entries)
