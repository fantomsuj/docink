import hashlib
from pathlib import Path
from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse

TRACKING_PARAMS = frozenset(
    {
        "utm_source",
        "utm_medium",
        "utm_campaign",
        "utm_term",
        "utm_content",
        "utm_id",
        "fbclid",
        "gclid",
        "msclkid",
        "mc_cid",
        "mc_eid",
        "ref",
        "ref_src",
        "_hsenc",
        "_hsmi",
    }
)


def canonical_uri(uri: str) -> str:
    """Return a canonical form of `uri` for stable ID generation.

    Strips tracking params, normalizes scheme/host casing, drops fragments,
    and resolves local file paths to absolute `file://` URIs.
    """
    parsed = urlparse(uri)

    if not parsed.scheme or parsed.scheme == "file":
        path = parsed.path if parsed.scheme == "file" else uri
        return "file://" + str(Path(path).expanduser().resolve())

    query_pairs = [
        (k, v)
        for k, v in parse_qsl(parsed.query, keep_blank_values=True)
        if k.lower() not in TRACKING_PARAMS
    ]
    query_pairs.sort()

    return urlunparse(
        (
            parsed.scheme.lower(),
            parsed.netloc.lower(),
            parsed.path.rstrip("/") or "/",
            "",
            urlencode(query_pairs),
            "",
        )
    )


def doc_id(canonical: str, length: int = 16) -> str:
    digest = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
    return f"sha256:{digest[:length]}"


def content_hash(body: str, length: int = 16) -> str:
    digest = hashlib.sha256(body.encode("utf-8")).hexdigest()
    return f"sha256:{digest[:length]}"
