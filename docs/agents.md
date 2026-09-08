# AI agents, MCP, and scheduled runs

Poyto can be exposed to conversational AI clients through MCP (Model Context Protocol). This keeps account credentials out of prompts and lets the agent call a small, explicit tool surface.

## Install

```bash
pip install -e '.[agent]'
```

Authenticate Poyto normally first. The recommended flow is to create the local persisted session with the CLI and then let MCP load that session automatically:

```bash
poyto login
poyto profile
```

Do not put access or refresh tokens in an AI prompt or MCP tool argument.

## Local agent / stdio MCP

```bash
poyto-mcp
```

A compatible local agent can launch that command as a stdio MCP server.

Example MCP launcher configuration:

```json
{
  "mcpServers": {
    "poyto": {
      "command": "poyto-mcp"
    }
  }
}
```

## Chat clients / HTTP MCP

For clients that support streamable HTTP MCP:

```bash
poyto-mcp --transport streamable-http --host 127.0.0.1 --port 8765
```

The default host is loopback only. If a cloud chat client must reach the server, put an authenticated HTTPS tunnel/reverse proxy in front of it. Do not expose the MCP port directly to the public internet.

Environment equivalents:

```text
POYTO_MCP_TRANSPORT=streamable-http
POYTO_MCP_HOST=127.0.0.1
POYTO_MCP_PORT=8765
```

## Tool surface

Read tools:

- `health`
- `profile`
- `balances`
- `portfolio`
- `markets`
- `market`
- `market_activity`
- `asset_price`
- `transactions`

Mutation tools:

- `buy`
- `sell`

Both mutation tools reject calls unless `confirm=true`. Agents should only set it after the user has explicitly confirmed the exact market, position and amount.

## Agent Skill

A reusable skill definition is included at:

```text
skills/poyto/SKILL.md
```

Agents that support repository skills can load that file directly. It documents tool selection, credential handling, mutation confirmation, and scheduling policy.

## Scheduling and automations

Scheduling belongs to the host agent/automation system rather than the Poyto client. Each scheduled run should call the MCP tools at execution time so it reads fresh server state.

Typical examples:

```text
Every day at 09:00, call balances and portfolio and summarize changes.
Every hour, inspect MARKET_ID and notify only if the requested condition is met.
Every evening, summarize the latest point transactions.
```

Read-only recurring jobs are the recommended default. Recurring buy/sell jobs should only be created when the user has explicitly requested the exact repeated transaction.

## Security model

The MCP layer deliberately does not expose login/token setters or Poyto's arbitrary raw HTTP request method. Credentials stay in the existing session/environment system, and high-impact state changes are restricted to explicit tools with confirmation gates.
