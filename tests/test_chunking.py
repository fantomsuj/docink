from docink.chunking import chunk_by_headings


def test_chunks_split_at_h2():
    md = "# Title\n\nIntro\n\n## Section A\n\nbody A\n\n## Section B\n\nbody B\n"
    chunks = chunk_by_headings(md)
    assert len(chunks) == 3
    assert chunks[0]["heading_path"] == ["Title"]
    assert chunks[1]["heading_path"] == ["Title", "Section A"]
    assert chunks[2]["heading_path"] == ["Title", "Section B"]


def test_chunk_ids_are_positional():
    md = "# A\n\ntext\n\n## B\n\nmore\n"
    chunks = chunk_by_headings(md)
    assert [c["chunk_id"] for c in chunks] == ["c0", "c1"]


def test_empty_markdown_returns_no_chunks():
    assert chunk_by_headings("") == []


def test_h3_does_not_split_by_default():
    md = "# A\n\n## B\n\n### C\n\ntext\n\n### D\n\nmore\n"
    chunks = chunk_by_headings(md)
    assert len(chunks) == 2
    assert "Section" not in [p for c in chunks for p in c["heading_path"]]
