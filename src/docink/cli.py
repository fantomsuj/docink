from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from docink.core import extract


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="docink",
        description="Extract any source to agent-readable markdown.",
    )
    parser.add_argument("uri", help="URL, file path, or YouTube link")
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit the full Document as JSON instead of markdown+frontmatter",
    )
    parser.add_argument(
        "--out",
        type=Path,
        help="Output directory; writes <id>.md and <id>.chunks.jsonl",
    )
    args = parser.parse_args(argv)

    try:
        doc = extract(args.uri)
    except NotImplementedError as e:
        print(f"docink: adapter not yet implemented: {e}", file=sys.stderr)
        return 2
    except Exception as e:
        print(f"docink: extraction failed: {e}", file=sys.stderr)
        return 1

    if args.out:
        args.out.mkdir(parents=True, exist_ok=True)
        slug = doc.id.replace(":", "_")
        (args.out / f"{slug}.md").write_text(doc.to_markdown_with_frontmatter())
        chunks_path = args.out / f"{slug}.chunks.jsonl"
        with chunks_path.open("w") as fh:
            for chunk in doc.chunks:
                fh.write(json.dumps(chunk.to_dict()) + "\n")
        print(f"Wrote {args.out / f'{slug}.md'}")
        print(f"Wrote {chunks_path} ({len(doc.chunks)} chunks)")
        return 0

    if args.json:
        print(json.dumps(doc.to_dict(), indent=2, default=str))
    else:
        print(doc.to_markdown_with_frontmatter())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
