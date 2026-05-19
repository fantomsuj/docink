# Using docink as an MCP server

`docink-mcp` is a stdio MCP server that exposes the library's `extract()`
function as a tool. Any MCP-capable agent (Claude Desktop, Cursor, Cline,
Continue, custom clients) can use it to pull URLs and files into markdown
without bundling `docink` itself.

## Install

```bash
pip install 'docink[all,mcp]'
```

You probably want `[all]` so the server can handle every source type. If
you only care about web extraction, `pip install 'docink[web,mcp]'` is
enough.

Readwise Reader support also requires the official CLI to be installed and
authenticated outside Python:

```bash
npm install -g @readwise/cli
readwise login
```

## Run

```bash
docink-mcp
```

The server speaks MCP over stdio. There's no daemon, no port, no config
file. The MCP client launches the process when it needs it.

## Tools exposed

The server keeps an in-process LRU+TTL cache of extracted documents
(default: 32 entries, 1h TTL) keyed by `doc_id`. The chunk-level tools
below all share that cache, so a typical agent flow — `list_chunks` to
see structure, then `get_chunk`/`search_chunks` to drill in — re-uses one
extraction.

### `extract(uri: str) -> dict`

Returns the full `Document` as a dict — markdown, metadata, chunks. Use
this when the agent wants structured access in one shot. For long
documents, prefer the chunk-level tools below so the full body doesn't
land in context.

### `extract_markdown(uri: str) -> str`

Returns just the markdown-with-frontmatter string. Use this when the agent
just wants to read the content.

### `list_chunks(uri: str) -> dict`

Indexes a document's chunks without returning their full text. Returns
`doc_id`, `chunk_count`, and one entry per chunk with `chunk_id`,
`heading_path`, line range, character count, and a short preview. Cheap
discovery step before `get_chunk`.

### `get_chunk(uri: str, chunk_id: str) -> dict`

Returns one addressable chunk by its `chunk_id` (e.g. `c3`). Re-uses the
cached extraction if the URI was fetched recently. On an unknown
`chunk_id`, raises with the list of available IDs.

### `search_chunks(uri: str, query: str, limit: int = 5) -> dict`

Ranks chunks by occurrences of the query terms (case-insensitive
substring; heading-path matches weighted higher) and returns the top
`limit` results with `chunk_id`, score, line range, and a snippet around
the first match. Use for "where in this doc is X" questions before
fetching full chunk text via `get_chunk`.

## Client configuration

### Claude Desktop

Edit `~/Library/Application Support/Claude/claude_desktop_config.json`
(macOS) or `%APPDATA%\Claude\claude_desktop_config.json` (Windows):

```json
{
  "mcpServers": {
    "docink": {
      "command": "docink-mcp"
    }
  }
}
```

If `docink-mcp` is in a venv that's not on the system PATH, use the
absolute path to the entry point:

```json
{
  "mcpServers": {
    "docink": {
      "command": "/path/to/.venv/bin/docink-mcp"
    }
  }
}
```

Restart Claude Desktop after editing.

### Cursor

Add to `~/.cursor/mcp.json` (or the project-local equivalent):

```json
{
  "mcpServers": {
    "docink": {
      "command": "docink-mcp"
    }
  }
}
```

### Claude Code

Add to your project's `.claude/settings.json` or user-level
`~/.claude/settings.json`:

```json
{
  "mcpServers": {
    "docink": {
      "command": "docink-mcp"
    }
  }
}
```

### Continue / Cline / other MCP clients

Most clients accept a similar `command` + optional `args` shape. Refer to
the client's MCP docs.

## Verifying the server works

```bash
# Manual smoke test — sends an MCP initialize request
echo '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test","version":"0.0.1"}}}' | docink-mcp
```

You should see a JSON response describing the server.

## Limitations

- **Adapter-owned auth.** The server pulls whatever URL you point it at.
  Authenticated sources handle auth inside the adapter. For example, the
  Readwise adapter relies on the user's local `readwise` CLI login.
- **In-process cache only.** Extracted documents are cached in memory
  for the life of the server process (default 32 entries, 1h TTL). The
  cache is dropped when the client disconnects and `docink-mcp` exits.
  Wrap with an external cache if you need persistence across sessions.
- **Process per call.** The agent launches `docink-mcp` once per session,
  but every fresh `extract` is a synchronous blocking fetch inside that
  process. Don't use it for high-volume crawling.

## Why not a remote HTTP server?

Local stdio is simpler to install and reason about, and most MCP clients
already speak it. If you need a hosted version, `docink` is small enough
that wrapping it in a FastAPI service is ~20 lines.
