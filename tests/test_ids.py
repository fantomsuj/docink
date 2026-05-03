from docink.ids import canonical_uri, content_hash, doc_id


def test_canonical_uri_strips_tracking_params():
    raw = "https://Example.com/Article?utm_source=twitter&id=42&fbclid=xyz"
    assert canonical_uri(raw) == "https://example.com/Article?id=42"


def test_canonical_uri_drops_fragment():
    assert canonical_uri("https://example.com/x#section") == "https://example.com/x"


def test_canonical_uri_sorts_query_for_stability():
    a = canonical_uri("https://example.com/x?b=2&a=1")
    b = canonical_uri("https://example.com/x?a=1&b=2")
    assert a == b


def test_doc_id_is_deterministic():
    canonical = "https://example.com/article"
    assert doc_id(canonical) == doc_id(canonical)
    assert doc_id(canonical).startswith("sha256:")


def test_doc_id_changes_with_uri():
    assert doc_id("https://example.com/a") != doc_id("https://example.com/b")


def test_content_hash_detects_changes():
    assert content_hash("hello") != content_hash("hello world")
    assert content_hash("same") == content_hash("same")
