from __future__ import annotations

from types import SimpleNamespace

from docink.adapters import readwise
from docink.registry import detect_source_type


def test_detects_readwise_inputs():
    assert detect_source_type("readwise://01gwfvp9pyaabcdgmx14f6ha0") == "readwise"
    assert detect_source_type("reader://01gwfvp9pyaabcdgmx14f6ha0") == "readwise"
    assert (
        detect_source_type("https://read.readwise.io/new/read/01gwfvp9pyaabcdgmx14f6ha0")
        == "readwise"
    )
    assert detect_source_type("readwise+https://example.com/article") == "readwise"


def test_readwise_adapter_fetches_document_details(monkeypatch):
    calls: list[list[str]] = []

    def fake_run(cmd, **kwargs):
        calls.append(cmd)
        if cmd == ["readwise", "--version"]:
            return SimpleNamespace(stdout="0.5.5\n")
        return SimpleNamespace(
            stdout=(
                "---\n"
                "id: 01gwfvp9pyaabcdgmx14f6ha0\n"
                "title: Reader Title\n"
                "author: Ada\n"
                "published_date: '2026-01-02'\n"
                "source_url: https://example.com/article\n"
                "word_count: 2\n"
                "---\n\n"
                "# Reader Title\n\nBody"
            )
        )

    monkeypatch.setattr(readwise.shutil, "which", lambda name: "/opt/homebrew/bin/readwise")
    monkeypatch.setattr(readwise.subprocess, "run", fake_run)

    result = readwise.extract("readwise://01gwfvp9pyaabcdgmx14f6ha0")

    assert calls[0] == [
        "readwise",
        "--json",
        "reader-get-document-details",
        "--document-id",
        "01gwfvp9pyaabcdgmx14f6ha0",
    ]
    assert result["markdown"] == "# Reader Title\n\nBody"
    assert result["title"] == "Reader Title"
    assert result["author"] == "Ada"
    assert result["published_at"].isoformat() == "2026-01-02T00:00:00"
    assert result["extractor"] == "readwise-cli@0.5.5"
    assert result["extras"]["reader_document_id"] == "01gwfvp9pyaabcdgmx14f6ha0"
    assert result["extras"]["source_url"] == "https://example.com/article"


def test_readwise_adapter_saves_url_then_fetches_details(monkeypatch):
    calls: list[list[str]] = []
    document_id = "01gwfvp9pyaabcdgmx14f6ha0"

    def fake_run(cmd, **kwargs):
        calls.append(cmd)
        if cmd == ["readwise", "--version"]:
            return SimpleNamespace(stdout="0.5.5\n")
        if "reader-create-document" in cmd:
            return SimpleNamespace(stdout=f'{{"id":"{document_id}"}}')
        return SimpleNamespace(
            stdout=(
                '{"content":"# Created\\n\\nBody","title":"Created",'
                f'"id":"{document_id}","url":"https://read.readwise.io/new/read/{document_id}"}}'
            )
        )

    monkeypatch.setattr(readwise.shutil, "which", lambda name: "/opt/homebrew/bin/readwise")
    monkeypatch.setattr(readwise.subprocess, "run", fake_run)

    result = readwise.extract("readwise+https://example.com/article?x=1")

    assert calls[0] == [
        "readwise",
        "--json",
        "reader-create-document",
        "--url",
        "https://example.com/article?x=1",
    ]
    assert calls[1] == [
        "readwise",
        "--json",
        "reader-get-document-details",
        "--document-id",
        document_id,
    ]
    assert result["markdown"] == "# Created\n\nBody"
    assert result["extras"]["created_from_url"] == "https://example.com/article?x=1"
