# MCP integration

Poyto has first-class, optional [Model Context Protocol (MCP)] support. The MCP layer is intentionally separate from the core HTTP client so applications that only use the Python API or CLI do not need the MCP runtime.

## Design

```text
POYP API
   ↑
resources / PoytoClient
   ↑
src/poyto/mcp/
   ├─ config.py      environment + CLI configuration
   ├─ server.py      FastMCP server + POYP tool registration
   └─ __main__.py    poyto-mcp entrypoint
```

`src/poyto/mcp_server.py` remains as a compatibility shim for code that imported the old module path.

MCP does not receive access tokens as tool arguments. It uses the same Poyto session/environment configuration as the Python client and CLI.

## Install

```bash
pip install -e '.[agent]'
```

## Recommended local setup

The default stdio transport is the easiest and safest local integration:

```bash
poyto-mcp
```

Most desktop MCP hosts should launch that command directly. No TCP port, public listener, or separate authentication layer is needed for stdio.

Check the effective non-secret MCP configuration before connecting a host:

```bash
poyto-mcp --print-config
```

Example output:

```json
{
  "host": "127.0.0.1",
  "port": 8765,
  "read_only": false,
  "transport": "stdio"
}
```

## Streamable HTTP

For a local HTTP MCP endpoint:

```bash
poyto-mcp --transport streamable-http --host 127.0.0.1 --port 8765
```

Do not bind an unauthenticated MCP process containing mutation tools directly to the public Internet. Put remote deployments behind a private MCP tunnel or a proper authenticated gateway.

## Read-only mode

Remote and research-only use should prefer read-only mode:

```bash
poyto-mcp --transport streamable-http --host 127.0.0.1 --port 8765 --read-only
```

or:

```bash
POYTO_MCP_READ_ONLY=true poyto-mcp
```

When read-only mode is enabled, account-changing tools are not registered at all.

## Environment variables

| Variable | Default | Purpose |
| --- | --- | --- |
| `POYTO_MCP_TRANSPORT` | `stdio` | `stdio`, `sse`, or `streamable-http` |
| `POYTO_MCP_HOST` | `127.0.0.1` | listener address for network transports |
| `POYTO_MCP_PORT` | `8765` | listener port |
| `POYTO_MCP_READ_ONLY` | `false` | omit mutation tools |

Normal Poyto authentication settings such as `POYTO_SESSION_FILE` continue to apply.

## Comfortable conversational tools

Poyto includes a few aggregate tools so an MCP host does not need to spend several round trips collecting routine context.

- `mcp_info`: shows server mode, available tool groups and mutation policy without exposing credentials.
- `account_snapshot`: returns profile, balances, portfolio, login-bonus state and unread notification count together. Prefer this for questions like “今の状態を見て” or “残高と保有をまとめて”.
- `market_context`: returns one market plus recent activity together. Prefer this before analysis of a specific market.

Smaller dedicated tools remain available when only one datum is needed. This keeps quick requests cheap while making broader conversational requests much smoother.

## Tool policy

Read tools include account/profile state, balances, portfolio, market discovery/detail/activity, POYP asset prices, transactions, login-bonus state, notification count and loss-gacha eligibility.

Mutation tools are only registered outside read-only mode. `buy`, `sell`, `settlement_claim`, loss-gacha ticket creation and loss-gacha claims require `confirm=true`. The MCP server rejects the mutation otherwise. `settlement_claim` accepts optional `coin_ratio` (0..100 in steps of 10) and `ticket_id`; when `coin_ratio` is supplied it uses the APK-static-established split-claim schema. Independent live-success evidence is still required for both settlement claim flows.

Tool annotations describe read-only/destructive/idempotent intent to capable MCP hosts. These annotations improve host behavior but are not treated as an authorization boundary; Poyto still enforces its own explicit confirmation requirement.

## Suggested host behavior

For the best conversational experience, an MCP host should:

1. call `mcp_info` once when it needs to understand the server mode;
2. prefer `account_snapshot` for general account questions;
3. prefer `market_context` for one-market analysis;
4. use `markets` only for discovery/listing;
5. use external web/search tools for real-world evidence instead of treating POYP prices as factual news evidence;
6. ask for explicit user confirmation immediately before any account-changing tool call.

## Web research

Poyto MCP is the source for POYP-specific account and market state. It deliberately does not pretend that POYP market prices are external evidence. A host such as ChatGPT should use its own web/search capability for current real-world facts, then keep those sources separate from Poyto data in its reasoning.

## Security boundary

The MCP package exposes Poyto operations only. Generic shell execution, arbitrary filesystem editing and Docker host-root control are deliberately not part of the default Poyto MCP server. If server administration is added later, it should live behind a separately named package/entrypoint, separate authentication and explicit deployment documentation rather than silently widening `poyto-mcp` authority.

Never paste access tokens, refresh tokens, HAR contents or session files into a chat. Configure authentication on the host running Poyto.
