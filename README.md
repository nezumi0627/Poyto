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

## Use from ChatGPT Web

**Portainer:** [日本語セットアップ](docs/setup-portainer.md) / [amd64（x64）用 YAML](compose.portainer.amd64.yaml) / [arm64 用 YAML](compose.portainer.arm64.yaml)

別の Linux マシンへの導入は **[日本語セットアップ手順](docs/setup-ja.md)** を参照してください。セッション移行、Tunnel 作成、ChatGPT 登録、常駐・自動起動、Docker 構成を説明しています。

Poyto Server Control exposes POYP tools, file edits and shell execution directly
through [OpenAI Secure MCP Tunnel](https://developers.openai.com/api/docs/guides/secure-mcp-tunnels).
Chat On Steroids is an interaction-model reference only, not a dependency.
Use `poyto-plugin --transport stdio` as the tunnel subprocess, or the Docker
loopback HTTP overlay. Follow [ChatGPT Web setup](docs/chatgpt-web.md) to configure
the tunnel and register the connection; writes are supported when the ChatGPT
workspace permits them. The CLI is available through the shell for operations
without a dedicated MCP wrapper.

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
- CI with Python 3.12 tests, Ruff, mypy, code statistics and package build; Python 3.10–3.14 compatibility tests on manual dispatch

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

The image starts **Poyto Server Control**, a standalone Streamable HTTP MCP endpoint that can be registered directly as a ChatGPT custom app. It combines the normal Poyto MCP tools with Linux server primitives inspired by Codex/Chat On Steroids Core: `read`, `apply_patch`, `exec_command`, and `write_stdin`. Chat On Steroids is only an implementation reference; it is not a runtime dependency and is not required for deployment.

Pull and run the published image:

```bash
docker pull ghcr.io/tqmane/poyto:latest
docker volume create poyto-data
docker run -d \
  --name poyto \
  --restart unless-stopped \
  -p 127.0.0.1:8765:8765 \
  -v poyto-data:/data \
  -v /srv/projects:/workspace \
  ghcr.io/tqmane/poyto:latest
```

The plugin endpoint is `/mcp` on port `8765`. It requires `Authorization: Bearer ...`; on first start a random token is created at `/data/control-plugin.token`. Retrieve it explicitly with:

```bash
docker exec poyto poyto-plugin-token
```

For ChatGPT Web, connect this endpoint directly as a custom MCP app. ChatGPT cannot connect straight to a loopback-only MCP server, so use OpenAI Secure MCP Tunnel for a private/on-prem deployment, or expose an authenticated HTTPS MCP endpoint. The POYP session remains separately persisted at `/data/session.json`.

For **Secure MCP Tunnel on the same Linux server**, start the loopback-only tunnel profile:

```bash
docker compose -f compose.yaml -f compose.secure-tunnel.yaml up -d --build
```

This uses host networking, removes Docker's published port, binds MCP only to `127.0.0.1:8765`, and disables the built-in static Bearer token. Use this mode only when Secure MCP Tunnel is the intended ingress. To combine it with root-equivalent host control, also add `-f compose.host-control.yaml`.

The built-in static Bearer token is useful for generic MCP clients and authenticated gateways. ChatGPT's current custom-app documentation explicitly covers direct MCP endpoints and OAuth; do not assume a particular ChatGPT account/UI can inject an arbitrary static Bearer token. For direct ChatGPT deployment, prefer Secure MCP Tunnel or an OAuth-capable authentication layer.

The normal container mode executes commands inside the container and confines file tools to `POYTO_PLUGIN_ROOTS` (default `/workspace:/data`). To grant full Linux-host command execution, explicitly layer the host-control compose file:

```bash
docker compose -f compose.yaml -f compose.host-control.yaml up -d --build
```

Host-control mode runs the plugin as root with `pid: host`, `privileged: true`, a writable `/host` bind, and `nsenter`. It is intentionally root-equivalent authority over the server. Never expose that endpoint without a private/authenticated transport and an authentication mechanism supported by the client or gateway.

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

For a first bootstrap, import the POYP authentication response from a `.har` or `.har.zip` capture made from an account/device you are authorized to use. If your Android device is already logged in and has working `su`, you can instead [extract its saved session over ADB](#android-adb--su-session-extraction) without a HAR capture.

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

### Android ADB + su session extraction

This procedure was verified on an already logged-in, rooted Android emulator on
2026-09-09. It reads POYP's saved session, not Apple credentials, and does not log
the app out. The observed storage location and schema are app-version-specific;
this is not a guaranteed method for every Android build or a way to perform the
initial Apple login.

Prerequisites: your own authorized POYP account is logged in in `com.poyp.poyp`,
ADB is installed on the Linux host, and `su` works on the device. The standalone
script uses only the Python 3.10+ standard library; installing Poyto is not needed
for extraction.

From the repository root, run:

```bash
python3 scripts/extract_android_session.py
```

With exactly one attached device, the script selects it automatically and checks
root access. Accept the Android USB-debugging/root prompt if shown, then rerun.
Keep the app idle during extraction. It saves credentials with mode `0600` to
`$XDG_STATE_HOME/poyto/android-session.json`, or
`~/.local/state/poyto/android-session.json` when `XDG_STATE_HOME` is unset.
If that default filename already exists, a new uniquely named file is created;
existing credentials are never overwritten. The script prints the saved path and
an import command, not the token values.

To choose a device or output file:

```bash
adb devices -l
python3 scripts/extract_android_session.py --serial DEVICE_SERIAL
python3 scripts/extract_android_session.py --output /absolute/private/path/session.json
```

`ANDROID_SERIAL` is also supported. Replace `DEVICE_SERIAL` with the intended
serial shown by ADB. An explicit `--output` must not already exist and must be
outside this repository.

The script checks for pending journal/WAL bytes and changes between two database
reads. If the app is writing, leave it idle and retry. The raw database is parsed
in a private temporary directory under `/tmp`, removed when parsing finishes;
only the session credentials and expiry fields remain in the output. The script
makes no POYP network calls, changes no Android files, and does not import into
or overwrite Poyto's active session automatically. Changed/encrypted app storage
is not supported; do not assume another storage format when extraction fails.

After extraction, use the exact path printed by the script to import into the
Poyto installation used by your plugin. For a checkout with `.venv`:

```bash
.venv/bin/poyto login @/absolute/path/printed/by/the/script.json
.venv/bin/poyto balances
```

Import and plugin must run as the same Linux user with the same
`POYTO_SESSION_FILE` setting. Docker has a separate session store: mount the
extracted JSON read-only and import it into the container's persistent `/data`
volume, as in the HAR bootstrap above, using `poyto login @/tmp/session.json`.

Extraction alone does not prove that the server still accepts the credentials.
An expired access token may be renewed by Poyto if the refresh token remains valid;
the `balances` call verifies access and may rotate the saved credentials. Do not
re-import an old extraction after rotation. Keep the extracted file outside Git and
chat, and remove it after successful import if you no longer need the extra copy.

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

Normal CI tests Python 3.12, matching the Docker runtime. Use Actions → CI → Run workflow for the full Python 3.10–3.14 compatibility matrix. Lint, type checking and package builds remain separate checks.

## Security

Never commit access tokens, refresh tokens, identity tokens, cookies, session files, HAR captures, or stable device identifiers. Keep sensitive local debugging artifacts outside the repository.

## License

MIT. See [LICENSE](LICENSE). The project disclaimer is in [DISCLAIMER.md](DISCLAIMER.md).
