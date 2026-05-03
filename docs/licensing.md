# Licensing — wrapping open-source projects

This doc explains how `docink` handles the licenses of the tools it wraps,
and what best practices apply when you build a project that depends on
other open-source software.

## TL;DR

- **`docink` is MIT-licensed.** Permissive — anyone can use, modify,
  redistribute, including in proprietary software.
- **All wrapped backends are permissive** (MIT / Apache 2.0 / Unlicense).
  No GPL, no AGPL, no copyleft contagion.
- **We don't vendor source.** Backends are installed via optional extras
  (`pip install docink[web]`), so the user pulls them from their authoritative
  source under their own license terms.
- **We attribute upstream** in [ATTRIBUTIONS.md](../ATTRIBUTIONS.md) and the
  README.

## Wrapped backend license matrix

| Backend | Used by | License | Notes |
|---|---|---|---|
| [trafilatura](https://github.com/adbar/trafilatura) | `web` adapter | Apache 2.0 | Permissive; requires NOTICE preservation if redistributed |
| [defuddle](https://github.com/kepano/defuddle) (npm) | `web` adapter (planned) | MIT | Permissive |
| [markitdown](https://github.com/microsoft/markitdown) | `pdf`, `office` adapters | MIT | Permissive |
| [docling](https://github.com/DS4SD/docling) | `pdf` adapter (planned) | MIT | Permissive |
| [yt-dlp](https://github.com/yt-dlp/yt-dlp) | `youtube` adapter | Unlicense | Public domain |
| [fastmcp](https://github.com/jlowin/fastmcp) | MCP server | Apache 2.0 | Permissive; NOTICE if redistributed |
| [pyyaml](https://pyyaml.org) | core | MIT | Permissive |

**No copyleft (GPL/AGPL/LGPL) dependencies anywhere.** If you add a
backend, check its license against this matrix before merging.

## License compatibility — what's safe to wrap

When you build on top of an open-source library, the relevant question is
whether *your* license is compatible with *theirs*. For permissive
licenses (MIT, Apache 2.0, BSD, ISC, Unlicense) the answer is "yes" in
nearly every direction — they impose attribution requirements but no
share-alike obligation.

The danger zone is copyleft licenses:

| License | Can you build a closed-source app on top? | Can you relicense your wrapper as MIT? |
|---|---|---|
| MIT, BSD, ISC, Apache 2.0, Unlicense | Yes | Yes |
| LGPL (Lesser GPL) | Yes, if dynamically linked / used as a library | Tricky; consult a lawyer |
| GPL | No — your code becomes GPL | No |
| AGPL | No, even for SaaS | No |

`docink` deliberately avoids GPL/AGPL backends. If a future adapter
*needs* a copyleft library, the right move is to:

1. Put it behind an extra (`docink[gpl-thing]`).
2. Document loudly in the adapter's docstring and README.
3. Note that users who install that extra are taking on the GPL terms
   for their distribution.

The `docink` package itself remains MIT regardless, because optional
extras are not bundled or distributed by us.

## Best practices for wrapping OSS

### 1. Don't vendor source code

The cleanest model is: declare the dependency in `pyproject.toml`, let pip
fetch it from PyPI, and never include the source tree in your repo. This
sidesteps redistribution obligations entirely.

If you *must* vendor (e.g., to patch a bug upstream hasn't merged), keep
the vendored copy in a clearly marked directory (`vendor/<name>/`),
preserve the original `LICENSE` and `NOTICE` files, and document the patch
in your CHANGELOG.

### 2. Preserve attribution

Every wrapped backend gets an entry in [ATTRIBUTIONS.md](../ATTRIBUTIONS.md)
with the project name, repo URL, license, and a one-line description of
what we use it for. The README links to it.

For Apache 2.0 dependencies, if you ever bundle their source, ship their
NOTICE file alongside yours. We don't bundle, so this is moot today —
but documenting it here so future-you doesn't lose track.

### 3. Use the upstream's distribution channel

Always `pip install thirdparty` from PyPI. Don't mirror their package on
your own index. Mirroring creates a redistribution obligation and a
maintenance burden you don't want.

### 4. Don't reuse upstream's branding

`docink` doesn't use "defuddle", "docling", or "markitdown" in the
user-facing names of its adapters — they're just `web`, `pdf`, `office`.
This avoids implying endorsement and keeps the wrapper free to swap
backends without renaming.

You *should* mention upstream by name in docs and the `extractor` field
of the schema (e.g., `"extractor": "trafilatura@1.12.0"`) — that's
attribution, which is the opposite of trademark abuse.

### 5. Track upstream

For each backend, pin a version range that you've tested
(`trafilatura>=1.12,<2`). Watch upstream issues for breaking changes
or CVEs. When you bump the pin, run the integration tests for that
adapter (when those exist).

### 6. Be explicit about what you don't do

`docink`'s README and architecture doc both state "we don't compete on
parser quality." That's both technically accurate and a courtesy to
upstream — we're not framing this as a replacement for the projects
we depend on.

### 7. License your own work permissively

If you publish a wrapper and want maximum adoption, MIT or Apache 2.0
removes the friction. GPL on a wrapper makes downstream users think
twice about depending on it.

## Edge cases worth knowing

### Apache 2.0 + patent grant

Apache 2.0 includes an explicit patent grant. This is mostly a feature
for users — but it means if you contribute to an Apache 2.0 project,
you're granting patent rights for your contribution. Not unique to
`docink`; just worth knowing.

### npm vs PyPI license discrepancy

When a package has both npm and PyPI distributions, the licenses can
differ. `defuddle` ships only on npm and is MIT there. Always check the
license on the actual distribution channel you're consuming, not just
the GitHub repo.

### "All rights reserved" with no LICENSE file

Some open-source-looking repos have no LICENSE file or are explicitly
"all rights reserved." These are **not** safe to depend on, even if the
code is on GitHub — without a license, the default is full copyright,
and you have no rights to use the code beyond what fair use covers.

If you find a backend you'd love to wrap that has no license, file an
issue asking the maintainer to add one before depending on it.

### Trademark considerations

Most permissive licenses include a clause excluding trademark rights.
You can use the *code* under the license, but you can't necessarily use
the *name/logo* freely. Practically: don't make a "docink-defuddle"
product without checking, and don't put upstream logos on your README
without permission.

## What we promise downstream users

The implicit contract for someone installing `docink`:

1. The core library (what `pip install docink` gives you) is MIT,
   pure Python, with one runtime dep (pyyaml/MIT).
2. Optional extras pull permissively-licensed backends from PyPI/npm
   under their own terms. You can audit each via the matrix above.
3. We won't add a copyleft dependency without bumping the major version
   and shouting in the changelog.

## Further reading

- [Choose a License](https://choosealicense.com) — practical license
  picker.
- [SPDX License List](https://spdx.org/licenses/) — canonical list of
  identifiers.
- [Open Source Initiative](https://opensource.org/licenses) — definitions
  and approved licenses.
- [Apache 2.0 NOTICE FAQ](https://www.apache.org/legal/src-headers.html#notice)
  — when and how to ship NOTICE files.
