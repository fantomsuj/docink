# Distribution — how others install and use docink

This doc covers how to ship `docink` to users and how end users wire it
into their own coding agents.

## Three audiences, three packaging stories

| Audience | Channel | Why |
|---|---|---|
| Python developers | PyPI (`pip install docink`) | Standard, lowest friction |
| Agent users (Claude Desktop, Cursor, Cline) | MCP server (`docink-mcp`) | One-line config, no Python knowledge needed |
| Self-contained / no-Python users | MCPB bundle (`.mcpb` file) | Includes Python runtime, double-click install |

The same source ships all three. PyPI is primary; the others build on top.

## 1. PyPI (primary)

The standard channel. Users install with `pip`:

```bash
pip install docink                  # core
pip install 'docink[all,mcp]'       # everything, including MCP server
```

### Releasing

```bash
# 0. Make sure CHANGELOG and version are updated
# 1. Build
python -m build

# 2. Test on TestPyPI first
twine upload --repository testpypi dist/*
pip install --index-url https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple/ docink

# 3. Publish to real PyPI
twine upload dist/*

# 4. Tag the release
git tag v0.1.0 && git push --tags
```

### CI/CD (planned)

`.github/workflows/release.yml` should:

1. Run `pytest` on every push.
2. On tag push (`v*`), build and `twine upload` to PyPI using a
   `PYPI_API_TOKEN` secret.
3. Cut a GitHub Release with the relevant `CHANGELOG.md` section as the
   body.

Not wired up yet; this is one of the first tasks for the next contributor.

## 2. GitHub repo

The source of truth. Standard layout:

```
docink/
├── .github/
│   ├── workflows/
│   │   ├── ci.yml          # pytest on push
│   │   └── release.yml     # PyPI publish on tag
│   └── ISSUE_TEMPLATE/
├── src/docink/
├── tests/
├── docs/
├── README.md
├── LICENSE
├── CHANGELOG.md
├── CONTRIBUTING.md
├── AGENTS.md
├── CLAUDE.md
├── pyproject.toml
└── ...
```

### Recommended repo settings

- **Branch protection on `main`** — require PR review, CI passing.
- **Semver tags** — `v0.1.0`, `v0.1.1`, etc. Trigger releases off these.
- **Discussions enabled** — for adapter requests and integration questions.
- **Issue templates** — bug report, adapter request, integration question.
- **Topics** — `mcp`, `markdown`, `extraction`, `agents`, `llm`, `python`.

## 3. MCP server config (the agent integration story)

This is what most users will actually use. Once they've `pip install`ed
`docink[all,mcp]`, they add a few lines to their MCP client config and
the agent gets URL/file ingestion.

See [docs/mcp.md](mcp.md) for client-by-client config examples (Claude
Desktop, Cursor, Cline, Claude Code, Continue).

### Why this matters

Agents that ingest external content typically reinvent extraction badly:
each tool wires up its own HTML parser, PDF parser, etc. Centralizing on
one MCP server means:

- One place to fix extraction bugs across all agents.
- Citations stay stable across agents (same `id` and `chunk_id`).
- New source types (e.g., a future Notion adapter) light up everywhere
  at once.

## 4. MCPB bundle (zero-Python install)

For non-developer users who want to use docink in Claude Desktop without
installing Python and pip themselves. The `mcpb` tool bundles a Python
runtime + `docink[all,mcp]` + the MCP manifest into a single `.mcpb` file
that Claude Desktop can install with a double-click.

Build:

```bash
# in the repo root, with mcpb installed
mcpb pack --python --include 'src/docink' --entry docink.mcp.server:main
# produces docink-X.Y.Z.mcpb
```

(Not yet wired up in CI; the `mcp-server-dev:build-mcpb` skill is the
fastest path.)

This is the "casual user" channel. PyPI is still the source of truth.

## 5. Claude Code plugin (optional)

For users who want `docink` available as a Claude Code skill rather than
an MCP tool. Lighter weight than MCP — pure markdown describing how to
invoke `docink-mcp`. The repo could ship a `plugin/` directory with:

```
plugin/
├── plugin.json              # plugin manifest
└── skills/
    └── docink/
        └── SKILL.md         # how to use docink for source capture
```

Users install via `claude plugin add github.com/<org>/docink`. This isn't
critical for v0.1 but is a low-effort add once the repo is on GitHub.

## 6. Direct from GitHub (no PyPI)

For users who want to pin to a specific commit or run pre-release code:

```bash
pip install git+https://github.com/<org>/docink@main
pip install git+https://github.com/<org>/docink@v0.1.0
```

This works without any extra setup since the repo is `pyproject.toml`-based.

## Versioning policy

- **0.x.y** — schema is allowed to change in minor versions. Users
  pinning should pin to `~=0.1.0`.
- **1.0+** — schema frozen. Field additions allowed; field removals or
  type changes require a major bump.
- Version is declared once in `pyproject.toml` and exported from
  `src/docink/__init__.py` as `__version__`.

## Distribution checklist for v0.1.0

- [ ] Move repo out of `sandbox/skolpuru/` into its own GitHub repo
- [ ] Update placeholder URLs in `pyproject.toml`
- [ ] Wire up GitHub Actions CI
- [ ] Publish `0.1.0a1` to TestPyPI to verify packaging
- [ ] Publish `0.1.0a1` to PyPI to claim the name
- [ ] Add MCP server config examples to README
- [ ] Build and attach an `.mcpb` bundle to the GitHub release
- [ ] (Optional) Submit to mcp-servers-list / awesome-mcp registries
