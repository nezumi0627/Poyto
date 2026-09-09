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

## Local stdio

The safest/default transport is stdio:

```bash
poyto-mcp
```

This is suitable for local MCP hosts that launch the server as a subprocess.

Equivalent explicit command:

```bash
poyto-mcp --transport stdio
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

## Tool policy

Read tools include account/profile state, balances, portfolio, market discovery/detail/activity, POYP asset prices, transactions, login-bonus state, notification count and loss-gacha eligibility.

Mutation tools are only registered outside read-only mode. `buy`, `sell`, loss-gacha ticket creation and loss-gacha claims require `confirm=true`. The MCP server rejects the mutation otherwise.

Tool annotations describe read-only/destructive/idempotent intent to capable MCP hosts. These annotations improve host behavior but are not treated as an authorization boundary; Poyto still enforces its own explicit confirmation requirement.

## Web research

Poyto MCP is the source for POYP-specific account and market state. It deliberately does not pretend that POYP market prices are external evidence. A host such as ChatGPT should use its own web/search capability for current real-world facts, then keep those sources separate from Poyto data in its reasoning.

## Security boundary

The MCP package exposes Poyto operations only. Generic shell execution, arbitrary filesystem editing and Docker host-root control are deliberately not part of the default Poyto MCP server. If server administration is added later, it should live behind a separately named package/entrypoint, separate authentication and explicit deployment documentation rather than silently widening `poyto-mcp` authority.

Never paste access tokens, refresh tokens, HAR contents or session files into a chat. Configure authentication on the host running Poyto.
