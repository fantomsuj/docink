# Writing an adapter

An adapter is one Python file under `src/docink/adapters/` that converts a
single source type to markdown plus metadata. Adapters are intentionally
trivial — no base class, no plugin system, no framework. Just a function.

## Contract

```python
def extract(uri: str) -> dict[str, Any]:
    ...
```

Returns a dict with these keys:

| Key | Type | Required | Notes |
|---|---|---|---|
| `markdown` | `str` | yes | The extracted body. May be empty if the source has no extractable text. |
| `title` | `str \| None` | yes | Set to `None` if the backend doesn't surface one. |
| `author` | `str \| None` | yes | |
| `published_at` | `datetime \| None` | yes | UTC if you can resolve it; naive otherwise. |
| `language` | `str \| None` | yes | BCP-47 if known. |
| `extractor` | `str \| None` | yes | `name@version` of the backend that did the work. |
| `extras` | `dict[str, Any]` | yes | Source-type-specific metadata. May be empty. Document the shape in [docs/schema.md](schema.md). |

The core wraps this dict into a `Document`, generates the `id` and
`content_hash`, runs chunking, and returns the assembled object. Adapters
don't see any of that.

## Failure handling

- Missing extras → raise `RuntimeError` with the exact `pip install`
  command. Example:
  ```python
  try:
      import trafilatura
  except ImportError as e:
      raise RuntimeError(
          "web adapter requires `pip install docink[web]` (trafilatura)"
      ) from e
  ```
- Backend returned nothing → raise `RuntimeError(f"...extracted no content from {uri}")`.
- Network/file errors → let them propagate. Don't wrap them in a generic
  exception that hides the cause.

## Web backend comparison

The web adapter uses `defuddle` first and falls back to `trafilatura`.
For benchmark harnesses or one-off comparisons, call:

```python
from docink.adapters.web import extract_with_backend

defuddle_doc = extract_with_backend(uri, backend="defuddle")
trafilatura_doc = extract_with_backend(uri, backend="trafilatura")
```

The returned dict shape is the same as `extract()`, so benchmark code can
compare output quality without special-casing backend payloads.

## Readwise Reader adapter

The `readwise` adapter is intentionally explicit because it uses an
authenticated, stateful service rather than a stateless extractor.

```bash
npm install -g @readwise/cli
readwise login

docink "readwise://READER_DOCUMENT_ID"
docink "https://read.readwise.io/new/read/READER_DOCUMENT_ID"
docink "readwise+https://example.com/article"
```

`readwise://...` and Reader document URLs fetch an existing saved document.
`readwise+https://...` first runs `readwise reader-create-document`, which
can mutate the user's Reader library, then fetches the created document's
Markdown with `reader-get-document-details`.

Do not register bare `https://...` URLs to the Readwise adapter. Normal web
extraction must remain account-free and non-mutating.

## Registry

Add detection logic in `src/docink/registry.py`:

```python
def detect_source_type(uri: str) -> str:
    ...
    if my_pattern_matches(uri):
        return "myadapter"
    ...
```

And dispatch:

```python
def get_adapter(source_type: str) -> ModuleType | None:
    from docink.adapters import office, pdf, web, youtube, myadapter
    return {..., "myadapter": myadapter}.get(source_type)
```

Detection is currently a series of `if`s on URL/path patterns. If it grows
past ~15 cases, consider a small declarative table.

## Dependencies

Add the backend under a new extras group in `pyproject.toml`:

```toml
[project.optional-dependencies]
myadapter = ["the-backend>=1.0"]
all = [..., "the-backend>=1.0"]
```

Never put the backend in core `dependencies`. Always optional, always behind
an import-guarded `RuntimeError`.

## Testing

Each adapter ships a golden fixture:

```
tests/fixtures/myadapter/
  input.html              # or whatever the source format is
  expected.md             # extracted markdown
  expected.metadata.json  # title, author, published_at, etc.
```

Unit test (no network):

```python
from pathlib import Path
from docink.adapters import myadapter

def test_myadapter_extracts_fixture():
    fixture = Path(__file__).parent / "fixtures" / "myadapter"
    result = myadapter.extract(str(fixture / "input.html"))
    assert result["title"] == "Expected Title"
    assert "expected substring" in result["markdown"]
```

Integration tests (live URLs) go behind a `pytest -m integration` marker
once that's wired up. Skip live tests by default.

## Adapters worth writing

In rough priority order:

1. **Slack export** — `.zip` from a Slack workspace export. Each channel
   becomes a document; messages with timestamps become chunks.
2. **Notion export** — markdown export from Notion. Mostly identity-pass
   but with frontmatter normalization.
3. **GitHub repo** — `https://github.com/owner/repo` → README + `docs/`
   + selected source files. Tricky: file selection heuristic.
4. **Plain HTML file** — local `.html` file, no fetch step. Currently
   `web` adapter handles this via trafilatura; could split for clarity.
5. **RSS / Atom feed** — feed URL → one document with chunks per entry.
6. **Gmail mbox** — local mbox export → one document per thread.
7. **arXiv** — recognize arxiv URLs and prefer the LaTeX source over
   the PDF when available.

## Things adapters should not do

- Cache. Caching is the caller's problem. An adapter `extract(uri)` should
  fetch fresh every time.
- Retry on network failure. The caller wraps with retry logic if they want
  it.
- Hash anything. The core computes `content_hash` from your returned
  markdown.
- Generate chunks. The core runs the shared chunker on your markdown.
  If your source has natural chunk boundaries (e.g., YouTube cues, Slack
  messages), encode them in markdown as headings or anchors and let the
  chunker pick them up.
