from __future__ import annotations

from pathlib import Path
from types import ModuleType
from urllib.parse import urlparse

OFFICE_EXTS = {".docx", ".pptx", ".xlsx", ".doc", ".ppt", ".xls"}


def detect_source_type(uri: str) -> str:
    parsed = urlparse(uri)

    if not parsed.scheme or parsed.scheme == "file":
        path_str = parsed.path if parsed.scheme == "file" else uri
        ext = Path(path_str).suffix.lower()
        if ext == ".pdf":
            return "pdf"
        if ext in OFFICE_EXTS:
            return "office"
        if ext in {".html", ".htm"}:
            return "web"
        return "unknown"

    host = parsed.netloc.lower()
    if "youtube.com" in host or host.endswith("youtu.be"):
        return "youtube"

    path_lower = parsed.path.lower()
    if path_lower.endswith(".pdf"):
        return "pdf"
    if Path(path_lower).suffix in OFFICE_EXTS:
        return "office"

    return "web"


def get_adapter(source_type: str) -> ModuleType | None:
    from docink.adapters import office, pdf, web, youtube

    return {
        "web": web,
        "pdf": pdf,
        "youtube": youtube,
        "office": office,
    }.get(source_type)
