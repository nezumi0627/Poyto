# Poyto documentation

Start here:

- [MCP integration](mcp.md) — local/remote MCP setup, read-only mode, tool policy and security
- [Docker](docker.md) — conservative container deployment for Poyto MCP
- [Architecture](architecture.md) — project structure and responsibility boundaries
- [Authentication](authentication.md) — session bootstrap and credentials
- [Configuration](configuration.md) — environment and runtime settings
- [Refresh tokens](refresh-tokens.md) — refresh behavior and evidence
- [Python API](python-api.md) — library usage
- [CLI](cli.md) — command-line reference
- [Capabilities](capabilities.md) — supported surface and evidence level
- [Known gaps](known-gaps.md) — unverified or intentionally unsupported behavior
- [Endpoints](endpoints.md) — observed POYP routes
- [Trading](trading.md) — buy/sell evidence and cautions
- [Agents](agents.md) — AI-agent workflows around Poyto
- [Service model and legal context](service-model-and-legal-context.md) — POYP Terms facts, age evidence, automation classification, and Japan legal context

Poyto separates its core POYP client from integrations. MCP lives in `src/poyto/mcp/`; generic host administration is intentionally not part of the default MCP server.
