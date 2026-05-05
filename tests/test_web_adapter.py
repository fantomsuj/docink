from __future__ import annotations

import sys
from types import SimpleNamespace

import pytest

from docink.adapters import web


def test_web_adapter_prefers_defuddle(monkeypatch):
    calls: list[list[str]] = []

    def fake_run(cmd, **kwargs):
        calls.append(cmd)
        return SimpleNamespace(
            stdout=(
                '{"content":"# Title\\n\\nBody","title":"Title","author":"Ada",'
                '"published":"2026-01-02T03:04:05Z","language":"en",'
                '"description":"Desc","domain":"example.com","site":"Example",'
                '"wordCount":2,"parseTime":7}'
            )
        )

    monkeypatch.setattr(web, "_defuddle_command", lambda: ["defuddle"])
    monkeypatch.setattr(web.subprocess, "run", fake_run)

    result = web.extract("https://example.com/article")

    assert calls == [
        ["defuddle", "parse", "--json", "--markdown", "https://example.com/article"]
    ]
    assert result["markdown"] == "# Title\n\nBody"
    assert result["title"] == "Title"
    assert result["author"] == "Ada"
    assert result["published_at"].isoformat() == "2026-01-02T03:04:05+00:00"
    assert result["language"] == "en"
    assert result["extractor"] == "defuddle@0.14.0"
    assert result["extras"]["domain"] == "example.com"


def test_web_adapter_falls_back_to_trafilatura(monkeypatch):
    def fake_defuddle(uri: str):
        raise RuntimeError("defuddle unavailable")

    fake_metadata = SimpleNamespace(
        title="Fallback Title",
        author="Grace",
        date="2026-01-02",
        language="en",
    )
    fake_trafilatura = SimpleNamespace(
        __version__="1.12.0",
        fetch_url=lambda uri: "<html>ok</html>",
        extract=lambda html, **kwargs: "Fallback body",
        extract_metadata=lambda html: fake_metadata,
    )

    monkeypatch.setattr(web, "_extract_defuddle", fake_defuddle)
    monkeypatch.setitem(sys.modules, "trafilatura", fake_trafilatura)

    result = web.extract("https://example.com/article")

    assert result["markdown"] == "Fallback body"
    assert result["extractor"] == "trafilatura@1.12.0"
    assert result["extras"]["fallback_from"] == "defuddle"
    assert result["extras"]["backend_attempts"] == [
        {"extractor": "defuddle", "error": "defuddle unavailable"}
    ]


def test_extract_with_backend_rejects_unknown_backend():
    with pytest.raises(ValueError, match="backend must be one of"):
        web.extract_with_backend("https://example.com", backend="readability")
