# Poyto

Unofficial typed Python client and CLI for **POYP**, reconstructed from traffic captured from an authorized POYP session.

> [!IMPORTANT]
> Poyto is not affiliated with or endorsed by POYP. The API is undocumented and may change without notice. Use it only with accounts and credentials you are authorized to access.

## What changed in 0.2

- Pythonic, responsibility-based package layout
- `PoytoClient(token=...)` accepts literal tokens and plaintext/JSON/dotenv token files
- First-class environment-variable configuration
- Automatic saved-session loading and refresh-token rotation handling
- One-time authenticated 401 refresh/retry
- CLI parser and command execution split from library code
- Resource modules split into account, markets, trades, social, discovery, and events
- Corrected observed BTC price route to `/api/prices/BTC`
- CI on Python 3.10–3.14 with pytest, Ruff, mypy, and package build

## Install

```bash
git clone https://github.com/nezumi0627/Poyto.git
cd Poyto
python -m venv .venv
pip install -e '.[dev]'
```

## Quick start

Literal token:

```python
from poyto import PoytoClient

with PoytoClient(token="YOUR_ACCESS_TOKEN") as client:
    print(client.profile())
```

Token file:

```python
from pathlib import Path
from poyto import PoytoClient

with PoytoClient(token=Path("token.txt")) as client:
    print(client.balances())
```

Supported token-file formats:

```text
ACCESS_TOKEN
REFRESH_TOKEN
```

```dotenv
POYTO_TOKEN=...
POYTO_REFRESH_TOKEN=...
```

```json
{
  "access_token": "...",
  "refresh_token": "...",
  "expires_at": 1790000000
}
```

You can also use `token_file="token.txt"`, `token="@token.txt"`, or `token="file:token.txt"`.

## Environment variables

The simplest setup is:

```powershell
$env:POYTO_TOKEN = "..."
$env:POYTO_REFRESH_TOKEN = "..."
poyto profile
```

or:

```powershell
$env:POYTO_TOKEN_FILE = "$HOME\\poyto-token.env"
poyto balances
```

`PoytoClient()` reads the same environment automatically:

```python
from poyto import PoytoClient

with PoytoClient() as client:
    print(client.profile())
```

Canonical variables include `POYTO_TOKEN`, `POYTO_ACCESS_TOKEN`, `POYTO_REFRESH_TOKEN`, `POYTO_TOKEN_FILE`, `POYTO_SESSION_FILE`, `POYTO_AUTO_REFRESH`, `POYTO_API_BASE`, `POYTO_AUTH_BASE`, `POYTO_TIMEOUT`, and device metadata variables. Historical `POYP_*` credential/device aliases remain supported. See [`docs/configuration.md`](docs/configuration.md).

## Persistent login

Save a token once:

```powershell
poyto login
```

Then use normal commands without passing a token:

```powershell
poyto profile
poyto balances
poyto markets --limit 20
```

Default session locations:

```text
Windows: %LOCALAPPDATA%/Poyto/session.json
Other:   $XDG_STATE_HOME/poyto/session.json
         or ~/.local/state/poyto/session.json
```

`POYTO_SESSION_FILE` overrides the location.

## Refresh tokens

When expiry metadata and a refresh token are available, Poyto refreshes shortly before expiry and persists the newly returned access/refresh pair. If an authenticated POYP request receives HTTP 401, Poyto attempts one refresh and retries the request once.

The supplied HARs directly showed POYP issuing a refresh token, but did not contain a refresh exchange. The refresh request therefore follows the standard Supabase/GoTrue flow used by the observed auth backend. See [`docs/refresh-tokens.md`](docs/refresh-tokens.md) for the exact distinction.

## API examples

```python
from poyto import PoytoClient

with PoytoClient() as client:
    print(client.profile())
    print(client.balances())
    print(client.markets(limit=20))
    print(client.market("MARKET_ID"))
    print(client.asset_price("BTC"))
```

Automatic pagination:

```python
with PoytoClient() as client:
    for market in client.iter_markets(limit=100):
        print(market["id"], market["title"])
```

Observed write operations include buy/sell, comments, likes, follow/unfollow, referral-code update, notification read-all, and ad-reward claim. The CLI requires `--yes` for state-changing commands.

```powershell
poyto buy MARKET_ID 1 10 --yes
poyto sell MARKET_ID 0 0.5 --yes
poyto comment MARKET_ID "hello" --yes
poyto follow USER_ID --yes
```

## Architecture

The implementation is intentionally split so each layer has one job:

```text
config -> credentials/session -> HTTP transport -> resources -> high-level client -> CLI
```

Resource methods live under `src/poyto/resources/`, transport/auth exchange under `_http.py`, lifecycle policy under `auto.py`, and CLI parsing/execution in separate modules. See [`docs/architecture.md`](docs/architecture.md).

## Documentation

- [Configuration and environment variables](docs/configuration.md)
- [Authentication and token loading](docs/authentication.md)
- [Refresh tokens](docs/refresh-tokens.md)
- [Architecture](docs/architecture.md)
- [Python API](docs/python-api.md)
- [CLI reference](docs/cli.md)
- [Observed endpoints](docs/endpoints.md)
- [Reverse-engineering notes](docs/reverse-engineering.md)
- [HAR diff notes](docs/har-diff-2026-09-08.md)
- [Security](SECURITY.md)
- [Contributing](CONTRIBUTING.md)

## Development

```bash
pip install -e '.[dev]'
pytest
ruff check .
mypy src/poyto
python -m build
```

CI validates Python 3.10–3.14.

## Security

Never commit HAR captures, access tokens, refresh tokens, Apple identity tokens, cookies, or stable device identifiers. Token/session files should remain outside the repository.

## License

MIT. See [LICENSE](LICENSE).
