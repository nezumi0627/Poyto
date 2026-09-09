# Poyto

Unofficial typed Python client, CLI, and optional MCP server for **POYP**.

> [!IMPORTANT]
> Poyto is an independent project and is not affiliated with, endorsed by, sponsored by, or otherwise connected to POYP. The service interface is undocumented and may change without notice. Use Poyto only with accounts, credentials, devices, and data you are authorized to access. See [DISCLAIMER.md](DISCLAIMER.md).

## Overview

Poyto turns the observed POYP HTTP surface into a reusable Python package instead of tying API behavior to one script or automation host.

```text
POYP API
   ↑
HTTP transport + session lifecycle
   ↑
resource modules
   ↑
PoytoClient
   ├─ Python API
   ├─ CLI
   └─ MCP
```

The project currently covers authentication/session persistence, account state, balances, portfolio, markets, activity, asset prices, trading, social features, notifications, rewards and selected discovery/event surfaces. Exact support and evidence level are tracked in [docs/capabilities.md](docs/capabilities.md) and [docs/known-gaps.md](docs/known-gaps.md).

## Install

```bash
git clone https://github.com/nezumi0627/Poyto.git
cd Poyto
python -m venv .venv
pip install -e '.[dev]'
```

For MCP / conversational-agent support:

```bash
pip install -e '.[agent]'
```

## Quick start

```python
from poyto import PoytoClient

with PoytoClient() as client:
    print(client.profile())
    print(client.balances())
    print(client.markets(limit=20))
```

The CLI uses the same session/configuration layer:

```bash
poyto profile
poyto balances
poyto markets --limit 20
```

State-changing CLI commands require explicit `--yes` where defined.

## Authentication and persistent sessions

A practical initial bootstrap is importing an authorized POYP authentication response from a `.har` or `.har.zip` capture:

```bash
poyto login --har capture.har.zip
poyto profile
```

Poyto stores the imported session outside the repository and can persist refreshed credentials when the server accepts the refresh token.

Default session locations:

```text
Windows: %LOCALAPPDATA%/Poyto/session.json
Other:   $XDG_STATE_HOME/poyto/session.json
         or ~/.local/state/poyto/session.json
```

`POYTO_SESSION_FILE` overrides the path. HAR files and session files may contain sensitive credentials; never commit or paste them into issues/chats.

See [Authentication](docs/authentication.md), [Configuration](docs/configuration.md), and [Refresh tokens](docs/refresh-tokens.md).

## MCP

Poyto includes first-class optional Model Context Protocol support under `src/poyto/mcp/`.

```text
src/poyto/mcp/
├─ config.py      environment + CLI settings
├─ server.py      FastMCP server and POYP tool registration
└─ __main__.py    poyto-mcp entrypoint
```

The old `poyto.mcp_server` module remains as a compatibility shim; new code should use `poyto.mcp`.

Start the default local stdio server:

```bash
poyto-mcp
```

Start a local Streamable HTTP endpoint:

```bash
poyto-mcp --transport streamable-http --host 127.0.0.1 --port 8765
```

For remote/research-only use, enable read-only mode so mutation tools are not registered:

```bash
poyto-mcp --transport streamable-http --host 127.0.0.1 --port 8765 --read-only
```

or set:

```bash
POYTO_MCP_READ_ONLY=true
```

Read tools expose POYP account/market state. Mutation tools such as `buy` and `sell` require an explicit `confirm=true` even when the server is not read-only. MCP tool annotations describe read/destructive intent to compatible hosts.

Poyto MCP deliberately does **not** mix generic filesystem/root-server control into the default server. The MCP endpoint is for POYP capabilities; generic shell or host administration should remain a separate trust boundary if introduced later.

Full setup, tool policy, environment variables, and security guidance: **[MCP integration](docs/mcp.md)**.

## What Poyto can do

- existing-token, HAR/HAR.zip, and supported Apple id-token authentication paths
- persistent sessions, expiry metadata, refresh handling, and one-time authenticated 401 retry
- profile, balances, portfolio/history, transactions, missions, streaks, campaigns and notifications
- market listing/detail/activity/charts/prices and portfolio positions
- buy/sell operations
- comments, replies, likes, follows and user/social reads
- selected discovery, event, reward, referral and loss-gacha surfaces
- Python API, CLI, MCP and reusable agent skill
- typed package metadata and network-free regression tests

See [Capability inventory](docs/capabilities.md) for the precise supported surface.

## What is not proven

Poyto intentionally separates observed behavior from assumptions. Important unknowns include service-side trading formulas, settlement/slippage/fees, complete rate-limit and anti-abuse behavior, several account/session edge cases, realtime/private messaging, moderation/market-admin APIs, and server-side reward eligibility rules.

See [Known gaps](docs/known-gaps.md).

## Referral

If you are new to POYP, the maintainer currently provides this referral:

- Referral link: https://poyp.go.link/fjwo2?referral_code=S-0627
- Invite code: `S-0627`

POYP controls reward amounts and eligibility and may change them. The maintainer may receive a referral reward when an eligible new account registers through the link/code.

## Project layout

```text
src/poyto/
├─ resources/       API responsibility modules
├─ mcp/             optional MCP integration
├─ _http.py         HTTP/auth exchange
├─ auto.py          client lifecycle + session policy
├─ client.py        low-level client composition
├─ cli*.py          CLI parser/dispatch/entrypoint
├─ har_loader.py    secret-aware HAR import
└─ session_store.py persistent session storage
```

Architecture details: [docs/architecture.md](docs/architecture.md).

## Documentation

- [MCP integration](docs/mcp.md)
- [Capability inventory](docs/capabilities.md)
- [Known gaps](docs/known-gaps.md)
- [Observed endpoints](docs/endpoints.md)
- [Android APK/Hermes endpoint inventory](docs/apk-endpoints.md)
- [Endpoint inventory workflow](docs/endpoint-inventory.md)
- [Trading](docs/trading.md)
- [Configuration](docs/configuration.md)
- [Authentication](docs/authentication.md)
- [Refresh tokens](docs/refresh-tokens.md)
- [Python API](docs/python-api.md)
- [CLI reference](docs/cli.md)
- [AI agents and scheduled runs](docs/agents.md)
- [Architecture](docs/architecture.md)
- [Reverse-engineering notes](docs/reverse-engineering.md)
- [Poyto agent skill](skills/poyto/SKILL.md)
- [Security](SECURITY.md)
- [Contributing](CONTRIBUTING.md)

## Development

```bash
pip install -e '.[dev]'
pytest
ruff check .
mypy src/poyto
python scripts/code_stats.py
python -m build
```

CI validates Python 3.10–3.14.

## Security

Never commit access tokens, refresh tokens, identity tokens, cookies, session files, HAR captures, tunnel credentials, or stable device identifiers. Keep remote MCP endpoints private or behind an appropriate authenticated transport. See [SECURITY.md](SECURITY.md).

## License

MIT. See [LICENSE](LICENSE).
