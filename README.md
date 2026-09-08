# Poyto

Unofficial typed Python client and CLI for **POYP**, reconstructed from traffic captured from an authorized POYP session.

> [!IMPORTANT]
> Poyto is not affiliated with or endorsed by POYP. The API is undocumented and may change without notice. Use it only with accounts and credentials you are authorized to access.

## What Poyto can do

Poyto currently covers the major observed POYP HTTP surfaces:

- authentication with an existing token and observed Apple id-token login
- local session persistence, expiry metadata, automatic refresh policy, and one-time 401 recovery
- account profile, balances, portfolio/history, transactions, missions, streaks, campaigns, notifications, referral data, blocked users, and walking-challenge status
- market listing/detail/related/auxiliary data, positions, activity, charts, and asset prices
- observed buy/sell operations
- comments, replies, edit/delete/like, follow/unfollow, user profiles and social history
- home/discovery, leaderboards, timeline/global-chat reads, and observed event submission
- observed ad-reward claim API, including the captured HTTP 200 response fields
- Python API plus CLI, with `--yes` confirmation for state-changing CLI commands
- token files, environment configuration, masked session inspection, typed package metadata, and network-free regression tests

The implementation is deliberately conservative: an existing method does not automatically mean the complete server behavior is known. See **[Capability inventory](docs/capabilities.md)** for the full implemented list and its evidence level.

## What is not proven

Poyto explicitly tracks things that are missing enough evidence instead of guessing them. Important examples include:

- the exact POYP refresh-token exchange has **not** appeared in the supplied HARs; refresh follows standard Supabase/GoTrue behavior and is documented as inferred
- unlike-comment, market administration/creation/resolution, realtime sockets, direct messaging, arbitrary moderation controls, and many mutation routes have not been observed
- trading-engine formulas, settlement, slippage, fees, rate limits, anti-abuse behavior, and complete error schemas are unknown
- ad-reward server-side eligibility/proof rules are unknown even though the `watch_ad` claim request and one HTTP 200 response were captured
- observed reward values such as 5 points and a 2/5 daily count are observations, not hard-coded universal constants

See **[Known gaps and unverified behavior](docs/known-gaps.md)** for the canonical do-not-claim list.

## Code size

Poyto keeps code-size accounting reproducible instead of manually estimating it. Run:

```bash
python scripts/code_stats.py
```

The script reports physical and non-blank lines for `src/poyto/**/*.py`, separates core modules from `resources/`, reports tests, and prints each source file. CI runs the same measurement on Python 3.14.

The detailed LOC snapshot and feature-to-code map live in [docs/capabilities.md](docs/capabilities.md).

## What changed in 0.2

- Pythonic, responsibility-based package layout
- `PoytoClient(token=...)` accepts literal tokens and plaintext/JSON/dotenv token files
- first-class environment-variable configuration
- automatic saved-session loading and refresh-token rotation handling
- one-time authenticated 401 refresh/retry
- CLI parser and command execution split from library code
- resource modules split into account, markets, trades, social, discovery, and events
- corrected observed BTC price route to `/api/prices/BTC`
- secret-safe session/token inspection helpers
- typed observed ad-reward success response
- CI on Python 3.10–3.14 with pytest, Ruff, mypy, code statistics, and package build

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

`PoytoClient()` reads the same environment automatically. Canonical variables include `POYTO_TOKEN`, `POYTO_ACCESS_TOKEN`, `POYTO_REFRESH_TOKEN`, `POYTO_TOKEN_FILE`, `POYTO_SESSION_FILE`, `POYTO_AUTO_REFRESH`, `POYTO_API_BASE`, `POYTO_AUTH_BASE`, `POYTO_TIMEOUT`, and device metadata variables. Historical `POYP_*` aliases remain supported. See [configuration](docs/configuration.md).

## Refresh tokens

When expiry metadata and a refresh token are available, Poyto refreshes shortly before expiry and persists the newly returned access/refresh pair. If an authenticated POYP request receives HTTP 401, Poyto attempts one refresh and retries the request once.

The supplied HARs directly showed POYP issuing a refresh token, but did not contain a POYP refresh exchange. The implementation therefore follows the standard Supabase/GoTrue flow used by the observed auth backend and labels that behavior **implemented/inferred**, not observed. See [refresh tokens](docs/refresh-tokens.md).

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
poyto claim-ad-reward --yes
```

## Architecture

```text
config -> credentials/session -> HTTP transport -> resources -> high-level client -> CLI
```

Resource methods live under `src/poyto/resources/`, transport/auth exchange under `_http.py`, lifecycle policy under `auto.py`, and CLI parsing/execution in separate modules. See [architecture](docs/architecture.md).

## Documentation

- [Capability inventory and code-size accounting](docs/capabilities.md)
- [Known gaps and unverified behavior](docs/known-gaps.md)
- [Configuration and environment variables](docs/configuration.md)
- [Authentication and token loading](docs/authentication.md)
- [Refresh tokens](docs/refresh-tokens.md)
- [Ad rewards](docs/ad-rewards.md)
- [Architecture](docs/architecture.md)
- [Python API](docs/python-api.md)
- [CLI reference](docs/cli.md)
- [Observed endpoints](docs/endpoints.md)
- [Reverse-engineering notes](docs/reverse-engineering.md)
- [HAR diff notes](docs/har-diff-2026-09-08.md)
- [AI/contributor guide](AGENTS.md)
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

Never commit HAR captures, access tokens, refresh tokens, Apple identity tokens, cookies, or stable device identifiers. Token/session files should remain outside the repository.

## License

MIT. See [LICENSE](LICENSE).
