# Poyto

Unofficial Python client and CLI for **POYP**, reconstructed from traffic captured from the user's own POYP session.

> [!IMPORTANT]
> This project is **not affiliated with or endorsed by POYP**. The API is undocumented and can change without notice. Use it only with accounts and credentials you are authorized to access.

## Highlights

- Apple/Supabase session exchange and refresh
- Profile, balances, portfolio, missions and notifications
- Market listing, detail, charts, activity and positions
- Buy and sell requests observed in real app traffic
- Comments, replies, edits, deletes and likes
- Follow/unfollow and public user data
- Referral APIs, rankings, global chat and walking challenge status
- Generic request escape hatch for newly observed endpoints
- Typed package layout, pytest tests, Ruff, mypy and GitHub Actions
- No HAR files, private tokens or device identifiers are committed

## Install

For development:

```bash
git clone https://github.com/nezumi0627/Poyto.git
cd Poyto
python -m venv .venv
```

Windows PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
pip install -e ".[dev]"
```

macOS/Linux:

```bash
source .venv/bin/activate
pip install -e '.[dev]'
```

## Quick start

Set an existing POYP access token:

```powershell
$env:POYP_ACCESS_TOKEN="..."
poyto profile
poyto balances
poyto markets --limit 20
```

Python:

```python
from poyto import PoytoClient

with PoytoClient.from_env() as client:
    profile = client.profile()
    markets = client.markets(limit=20)
    print(profile)
    print(markets)
```

## Authentication

The captured app flow was:

```text
Sign in with Apple
       │
       ▼
auth.poyp.app / Supabase Auth
       │
       ▼
access_token + refresh_token
       │
       ▼
Authorization: Bearer <access_token>
       │
       ▼
api.poyp.app
```

Observed Apple exchange:

```powershell
$env:POYP_APPLE_ID_TOKEN="..."
$env:POYP_APPLE_ACCESS_TOKEN="..."
$env:POYP_APPLE_NONCE="..."
poyto login-apple
```

The CLI masks returned tokens instead of printing them in full. See [`docs/authentication.md`](docs/authentication.md).

## Market data

```powershell
poyto markets --limit 100 --sort recommended
poyto market MARKET_ID
poyto activity MARKET_ID --types comment
poyto charts MARKET_ID --tf max
poyto price BTC
```

Automatic pagination is available in Python:

```python
with PoytoClient.from_env() as client:
    for market in client.iter_markets(limit=100):
        print(market["id"], market["title"])
```

## Account-changing actions

The CLI requires `--yes` for state-changing operations.

```powershell
poyto buy MARKET_ID 1 10 --yes
poyto sell MARKET_ID 0 0.5 --yes
poyto comment MARKET_ID "hello" --yes
poyto follow USER_ID --yes
```

These calls can affect points, positions or account state. Verify arguments before running them.

## Device headers

The observed app sends device/app metadata headers. Configure them with environment variables when needed:

```text
POYP_APP_VERSION
POYP_OS
POYP_OS_VERSION
POYP_DEVICE_MODEL
POYP_DEVICE_ID
POYP_VENDOR_ID
POYP_OTA_GENERATION
POYP_IS_DEVICE
```

No device-specific value from the supplied HAR captures is committed.

## Documentation

- [Authentication](docs/authentication.md)
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
```

CI runs the test suite and Ruff on Python 3.10–3.13.

## Scope and limitations

This repository implements only endpoints and request shapes directly observed in the supplied captures. An endpoint being present here does **not** mean it is stable or officially supported. Where an operation has not been observed, the client intentionally avoids inventing a dedicated method.

## Security

Never commit HAR captures, access tokens, refresh tokens, Apple identity tokens, cookies or stable device identifiers. The `.gitignore` blocks common HAR and environment-secret files, but you should still review commits before pushing.

If a credential from an old HAR may still be valid, revoke/rotate it before sharing the HAR with anyone.

## License

MIT. See [LICENSE](LICENSE).
