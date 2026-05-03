import re
from dataclasses import dataclass

HEADING_RE = re.compile(r"^(#{1,6})\s+(.+?)\s*$")


@dataclass
class _RawChunk:
    start_line: int
    end_line: int
    heading_path: list[str]
    text: str


def chunk_by_headings(markdown: str, split_at_level: int = 2) -> list[dict]:
    """Split markdown into chunks at heading boundaries of `split_at_level` or shallower.

    Returns a list of chunk dicts with `chunk_id`, `start_line`, `end_line`,
    `heading_path`, and `text`. Chunk IDs are positional (`c0`, `c1`, ...) so
    they are stable as long as document structure is stable.
    """
    lines = markdown.splitlines()
    chunks: list[_RawChunk] = []
    heading_stack: list[tuple[int, str]] = []
    current_start = 0
    current_path: list[str] = []

    def flush(end_line: int) -> None:
        if end_line <= current_start:
            return
        text = "\n".join(lines[current_start:end_line]).strip()
        if not text:
            return
        chunks.append(
            _RawChunk(
                start_line=current_start + 1,
                end_line=end_line,
                heading_path=list(current_path),
                text=text,
            )
        )

    for i, line in enumerate(lines):
        match = HEADING_RE.match(line)
        if not match:
            continue
        level = len(match.group(1))
        title = match.group(2)

        if level <= split_at_level:
            flush(i)
            current_start = i

        while heading_stack and heading_stack[-1][0] >= level:
            heading_stack.pop()
        heading_stack.append((level, title))
        current_path = [t for _, t in heading_stack]

    flush(len(lines))

    return [
        {
            "chunk_id": f"c{idx}",
            "start_line": c.start_line,
            "end_line": c.end_line,
            "heading_path": c.heading_path,
            "text": c.text,
        }
        for idx, c in enumerate(chunks)
    ]
