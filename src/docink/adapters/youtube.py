from __future__ import annotations

import io
from datetime import datetime
from typing import Any


def extract(uri: str) -> dict[str, Any]:
    """Extract a YouTube video transcript with timestamp anchors.

    Output preserves `[hh:mm:ss]` markers at segment boundaries so chunks remain
    seekable back to the source video.
    """
    try:
        import yt_dlp
    except ImportError as e:
        raise RuntimeError(
            "youtube adapter requires `pip install docink[youtube]` (yt-dlp)"
        ) from e

    opts = {
        "skip_download": True,
        "writesubtitles": True,
        "writeautomaticsub": True,
        "subtitleslangs": ["en"],
        "subtitlesformat": "vtt",
        "quiet": True,
        "no_warnings": True,
    }
    with yt_dlp.YoutubeDL(opts) as ydl:
        info = ydl.extract_info(uri, download=False)

    subs = info.get("subtitles") or info.get("automatic_captions") or {}
    en_subs = subs.get("en") or next(iter(subs.values()), [])
    if not en_subs:
        raise RuntimeError(f"No transcript available for {uri}")

    vtt_url = en_subs[-1]["url"]

    import urllib.request

    with urllib.request.urlopen(vtt_url) as resp:
        vtt = resp.read().decode("utf-8", errors="replace")

    markdown = _vtt_to_markdown(vtt, title=info.get("title", "Untitled"))

    upload_date = info.get("upload_date")
    published_at: datetime | None = None
    if upload_date and len(upload_date) == 8:
        try:
            published_at = datetime.strptime(upload_date, "%Y%m%d")
        except ValueError:
            published_at = None

    return {
        "markdown": markdown,
        "title": info.get("title"),
        "author": info.get("uploader"),
        "published_at": published_at,
        "language": info.get("language") or "en",
        "extractor": f"yt-dlp@{yt_dlp.version.__version__}",
        "extras": {
            "video_id": info.get("id"),
            "duration_seconds": info.get("duration"),
            "channel": info.get("channel"),
        },
    }


def _vtt_to_markdown(vtt: str, title: str) -> str:
    """Minimal VTT → markdown with [hh:mm:ss] anchors per cue."""
    out = io.StringIO()
    out.write(f"# {title}\n\n")
    for block in vtt.split("\n\n"):
        lines = [ln for ln in block.splitlines() if ln.strip()]
        if not lines:
            continue
        timing = next((ln for ln in lines if "-->" in ln), None)
        if not timing:
            continue
        start = timing.split("-->")[0].strip().split(".")[0]
        text_lines = [ln for ln in lines if "-->" not in ln and not ln.strip().startswith("WEBVTT")]
        if not text_lines:
            continue
        text = " ".join(text_lines).strip()
        out.write(f"[{start}] {text}\n\n")
    return out.getvalue().rstrip() + "\n"
