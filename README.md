# Poyto

Unofficial typed Python client and CLI for **POYP**.

> [!IMPORTANT]
> Poyto is an independent project and is not affiliated with, endorsed by, sponsored by, or otherwise connected to POYP. The service interface is undocumented and may change without notice. Use the project only with accounts, credentials, devices, and data you are authorized to access. See [DISCLAIMER.md](DISCLAIMER.md).

## Try POYP

If you are new to POYP, you can use the maintainer's referral link/code below. Under POYP's current referral offer, a successful eligible registration is shown as awarding **400 points to both the new user and the referrer**. Referral rewards and eligibility are controlled by POYP and may change.

- Referral link: https://poyp.go.link/fjwo2?referral_code=S-0627
- Invite code: `S-0627`

> This is a referral link: the maintainer may receive 400 points when an eligible new user registers through it.

### 400 → 1,000 point goal

Poyto documents an optional point-growth workflow that can treat the **400 referral points** (or a configured bankroll of up to 500 points) as total managed capital and aim for a **1,000-point balance**. It avoids all-in entries, refreshes an expired session automatically, considers only evidence-backed positions with a projected gross payout of at least 2x, and stops opening new positions once the target is reached. This is a target, not a guaranteed return. See [Point bankroll growth goal](docs/bankroll-growth-goal.md).

## What Poyto can do

Poyto currently covers the major supported POYP HTTP surfaces:

- authentication with an existing token, `.har` / `.har.zip` session import, and Apple id-token exchange when the Apple credentials are already available
- local session persistence, expiry metadata, automatic refresh policy, and one-time 401 recovery
- account profile, balances, portfolio/history, transactions, missions, streaks, campaigns, notifications, referral data, blocked users, and walking-challenge status
- market listing/detail/related/auxiliary data, positions, activity, charts, and asset prices
- buy/sell operations
- comments, replies, edit/delete/like, follow/unfollow, user profiles and social history
- home/discovery, leaderboards, timeline/global-chat reads, and event submission
- ad-reward claim API, including typed successful response fields
- Python API plus CLI, with `--yes` confirmation for state-changing CLI commands
- token files, environment configuration, masked session inspection, typed package metadata, and network-free regression tests
- optional MCP server and reusable agent skill for conversational AI clients and scheduled automation hosts

See [Capability inventory](docs/capabilities.md) for the per-file breakdown and evidence level of every major feature.

## What is not proven

Poyto explicitly tracks behavior that is not sufficiently established instead of guessing it. Important examples include:

- automatically obtaining the initial Apple credentials without a HAR capture is still research in progress
- POYP-specific refresh-token reuse windows, inactivity/session limits, simultaneous-refresh behavior, and all revoked/expired-token errors are not fully established
- unlike-comment, market administration/creation/resolution, realtime sockets, direct messaging, arbitrary moderation controls, and many mutation routes are not currently supported
- trading-engine formulas, settlement, slippage, fees, rate limits, anti-abuse behavior, and complete error schemas are unknown
- ad-reward server-side eligibility/proof rules are unknown even though the `watch_ad` claim request and a successful response shape are implemented
- reward values and daily limits are treated as server-provided values rather than hard-coded universal constants

See [Known gaps and unverified behavior](docs/known-gaps.md) for the canonical do-not-claim list.

## Code size

Run:

```bash
python scripts/code_stats.py
```

It reports physical and non-blank lines for `src/poyto/**/*.py`, separates core modules from `resources/`, reports tests, and prints each source file. CI runs the same measurement on Python 3.14.

## What changed in 0.2

- Pythonic, responsibility-based package layout
- `PoytoClient(token=...)` accepts literal tokens and plaintext/JSON/dotenv token files
- first-class environment-variable configuration
- HAR/HAR.zip session import for practical initial bootstrap from authorized POYP traffic captures
- automatic saved-session loading and refresh-token rotation handling
- one-time authenticated 401 refresh/retry
- CLI parser and command execution split from library code
- resource modules split into account, markets, trades, social, discovery, and events
- corrected BTC price route to `/api/prices/BTC`
- secret-safe session/token inspection helpers
- typed ad-reward success response
- CI on Python 3.10–3.14 with pytest, Ruff, mypy, code statistics, and package build

## Install

```bash
git clone https://github.com/nezumi0627/Poyto.git
cd Poyto
python -m venv .venv
pip install -e '.[dev]'
```

For conversational AI / MCP support:

```bash
pip install -e '.[agent]'
poyto-mcp
```

See [AI agents, MCP, and scheduled runs](docs/agents.md) and the reusable [`skills/poyto/SKILL.md`](skills/poyto/SKILL.md).

## Docker

GitHub Actions publishes a multi-architecture image to `ghcr.io/tqmane/poyto`. The image contains both `linux/amd64` and `linux/arm64` variants, built on native GitHub-hosted x64 and Arm64 runners rather than through QEMU emulation.

Pull and run the published image:

```bash
docker pull ghcr.io/tqmane/poyto:latest
docker volume create poyto-data
docker run -d \
  --name poyto \
  --restart unless-stopped \
  -p 127.0.0.1:8765:8765 \
  -v poyto-data:/data \
  ghcr.io/tqmane/poyto:latest
```

The container serves the Streamable HTTP MCP endpoint at `/mcp` on port `8765` and stores its session at `/data/session.json`, so credentials survive container recreation without being baked into the image. Remote Docker deployments default to `POYTO_MCP_READ_ONLY=true`; set it to `false` only for MCP clients that should be allowed to see mutation tools.

GitHub Container Registry creates a newly published package as private by default. If anonymous pulls are desired, set the `poyto` package visibility to **Public** in GitHub after its first publication.

For the initial HAR bootstrap, use the same persistent volume and mount the capture read-only:

```bash
docker run --rm \
  -v poyto-data:/data \
  -v /absolute/path/to/capture.har.zip:/tmp/capture.har.zip:ro \
  ghcr.io/tqmane/poyto:latest \
  poyto login --har /tmp/capture.har.zip
```

The repository also includes `compose.yaml` for local builds/development:

```bash
docker compose up -d --build
docker compose ps
```

On pushes to `main`, version tags, and manual workflow runs, `.github/workflows/docker.yml` publishes to GHCR. Pull requests build both architectures without publishing. Release tags such as `v1.2.3` additionally produce `1.2.3`, `1.2`, and `1` image tags; the default branch produces `latest`, and every published build gets a `sha-*` tag.

If access is needed from another machine, keep the MCP port behind an authenticated HTTPS reverse proxy/tunnel rather than exposing it directly to the public internet. For ChatGPT Web setup and the intended Poyto + web-search workflow, see [ChatGPT Web + Poyto MCP](docs/chatgpt-web.md).

## Quick start

```python
from poyto import PoytoClient

with PoytoClient(token="YOUR_ACCESS_TOKEN") as client:
    print(client.profile())
    print(client.balances())
```

Token files may be plaintext, dotenv, or JSON. You can also use `token_file="token.txt"`, `token="@token.txt"`, or `token="file:token.txt"`.

## Persistent login

For a first bootstrap, the currently reliable path is to import the POYP authentication response from a `.har` or `.har.zip` capture made from an account/device you are authorized to use:

```powershell
poyto login --har "capture.har.zip"
poyto profile
poyto balances
poyto markets --limit 20
```

Python code can do the same:

```python
from poyto import PoytoClient

with PoytoClient() as client:
    client.login_from_har("capture.har.zip")
    print(client.profile())
```

The imported session is stored outside the repository. Once a refresh token is saved, Poyto can maintain the session through the live-verified POYP refresh exchange while that credential remains valid, so another HAR capture is not normally needed.

You can also persist an access token manually with `poyto login` or the Python token APIs documented in [Authentication](docs/authentication.md).

Default session locations:

```text
Windows: %LOCALAPPDATA%/Poyto/session.json
Other:   $XDG_STATE_HOME/poyto/session.json
         or ~/.local/state/poyto/session.json
```

`POYTO_SESSION_FILE` overrides the location.

Real HAR captures can contain cookies, authorization headers, tokens, device identifiers, and unrelated private traffic. Keep them outside the repository and do not attach them to issues or CI logs.

## Environment variables

Common variables include `POYTO_TOKEN`, `POYTO_ACCESS_TOKEN`, `POYTO_REFRESH_TOKEN`, `POYTO_TOKEN_FILE`, `POYTO_SESSION_FILE`, `POYTO_AUTO_REFRESH`, `POYTO_API_BASE`, `POYTO_AUTH_BASE`, `POYTO_TIMEOUT`, and device metadata variables. Historical `POYP_*` aliases remain supported. See [configuration](docs/configuration.md).

## Refresh tokens

When expiry metadata and a refresh token are available, Poyto refreshes shortly before expiry and persists the newly returned access/refresh pair. If an authenticated POYP request receives HTTP 401, Poyto attempts one refresh and retries the request once.

The exchange used by Poyto — `POST https://auth.poyp.app/auth/v1/token?grant_type=refresh_token` with the refresh token in the JSON body — was live-verified on 2026-09-09 using an existing authorized POYP session, and the returned session successfully authenticated a subsequent POYP API request. Project-specific lifetime, reuse, concurrency, and invalidation policies remain partially unknown. See [refresh tokens](docs/refresh-tokens.md).

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

State-changing operations include buy/sell, comments, likes, follow/unfollow, referral-code update, notification read-all, and ad-reward claim. The CLI requires `--yes` for state-changing commands.

```powershell
poyto buy MARKET_ID 1 10 --yes
poyto sell MARKET_ID 0 0.5 --yes
poyto comment MARKET_ID "hello" --yes
poyto follow USER_ID --yes
poyto claim-ad-reward --yes
```

## Architecture

```text
config -> credentials/session -> HTTP transport -> resources -> high-level client -> CLI/MCP
```

Resource methods live under `src/poyto/resources/`, transport/auth exchange under `_http.py`, lifecycle policy under `auto.py`, HAR session extraction under `har_loader.py`, CLI parsing/execution in separate modules, and the optional conversational-agent bridge in `mcp_server.py`. See [architecture](docs/architecture.md).

## Documentation

- [Capability inventory and LOC breakdown](docs/capabilities.md)
- [Known gaps and unverified behavior](docs/known-gaps.md)
- [Observed endpoints](docs/endpoints.md)
- [Trading API evidence](docs/trading.md)
- [Android APK/Hermes endpoint inventory](docs/apk-endpoints.md)
- [Endpoint inventory workflow](docs/endpoint-inventory.md)
- [Configuration](docs/configuration.md)
- [Authentication](docs/authentication.md)
- [Refresh tokens](docs/refresh-tokens.md)
- [Ad rewards](docs/ad-rewards.md)
- [Point bankroll growth goal](docs/bankroll-growth-goal.md)
- [Architecture](docs/architecture.md)
- [Python API](docs/python-api.md)
- [CLI reference](docs/cli.md)
- [AI agents, MCP, and scheduled runs](docs/agents.md)
- [Reverse-engineering notes](docs/reverse-engineering.md)
- [Poyto agent skill](skills/poyto/SKILL.md)
- [AI/contributor guide](AGENTS.md)
- [Disclaimer](DISCLAIMER.md)
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

Never commit access tokens, refresh tokens, identity tokens, cookies, session files, HAR captures, or stable device identifiers. Keep sensitive local debugging artifacts outside the repository.

## License

MIT. See [LICENSE](LICENSE). The project disclaimer is in [DISCLAIMER.md](DISCLAIMER.md).
