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

## Run

```bash
docink-mcp
```

The server speaks MCP over stdio. There's no daemon, no port, no config
file. The MCP client launches the process when it needs it.

## Tools exposed

### `extract(uri: str) -> dict`

Returns the full `Document` as a dict — markdown, metadata, chunks. Use
this when the agent wants structured access (e.g., to address a specific
chunk).

### `extract_markdown(uri: str) -> str`

Returns just the markdown-with-frontmatter string. Use this when the agent
just wants to read the content.

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

- **No auth.** The server pulls whatever URL you point it at. If you need
  authenticated sources (Google Drive, Notion, Slack), the adapter has to
  handle that — it's not at the MCP layer.
- **Single-shot.** Each `extract` call fetches fresh. There's no caching.
  Wrap with a caching MCP middleware if you need it.
- **Process per call.** The agent launches `docink-mcp` once per session,
  but every `extract` call is a synchronous blocking fetch inside that
  process. Don't use it for high-volume crawling.

## Why not a remote HTTP server?

Local stdio is simpler to install and reason about, and most MCP clients
already speak it. If you need a hosted version, `docink` is small enough
that wrapping it in a FastAPI service is ~20 lines.
