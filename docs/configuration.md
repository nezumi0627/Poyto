# Configuration

Poyto resolves configuration in a predictable order: **explicit Python/CLI arguments → explicit token source/file → environment variables → saved session → defaults**.

## Credentials

Canonical environment variables:

| Variable | Purpose |
| --- | --- |
| `POYTO_TOKEN` | Access token or token-file source (`@file`, `file:path`, existing path) |
| `POYTO_ACCESS_TOKEN` | Access-token alias |
| `POYTO_REFRESH_TOKEN` | Refresh token paired with an environment-provided access token |
| `POYTO_TOKEN_FILE` | Plaintext, JSON, or dotenv-style token file |
| `POYTO_SESSION_FILE` | Override persistent session file location |
| `POYTO_DEVICE_FILE` | Override persistent app-style device-ID file location |
| `POYTO_AUTO_LOAD_SESSION` | `true`/`false`; load saved session automatically |
| `POYTO_AUTO_REFRESH` | `true`/`false`; refresh near expiry and retry one authenticated 401 |
| `POYTO_SAVE_SESSION` | `true`/`false`; persist login/refresh results |

Compatibility aliases remain supported: `POYP_ACCESS_TOKEN`, `POYP_REFRESH_TOKEN`, and `POYP_TOKEN_FILE`.

Explicit credentials never silently borrow a refresh token from a different source. For example, `PoytoClient(token="...")` will not pair that token with `POYTO_REFRESH_TOKEN` unless the access token itself came from the environment.

## API and auth transport

| Variable | Purpose |
| --- | --- |
| `POYTO_API_BASE` | Override `https://api.poyp.app` |
| `POYTO_AUTH_BASE` | Override `https://auth.poyp.app` |
| `POYTO_SUPABASE_KEY` | Override the observed publishable Supabase key |
| `POYTO_TIMEOUT` | HTTP timeout in seconds |

`POYP_API_BASE`, `POYP_AUTH_BASE`, `POYP_SUPABASE_KEY`, and `POYP_TIMEOUT` are accepted as aliases.

## Apple exchange

`poyto login-apple` also reads:

- `POYTO_APPLE_ID_TOKEN` / `POYP_APPLE_ID_TOKEN`
- `POYTO_APPLE_ACCESS_TOKEN` / `POYP_APPLE_ACCESS_TOKEN`
- `POYTO_APPLE_NONCE` / `POYP_APPLE_NONCE`

## Device metadata

Every observed POYP device header can be configured with either canonical `POYTO_*` or compatibility `POYP_*` names:

- `POYTO_APP_VERSION`
- `POYTO_OS`
- `POYTO_OS_VERSION`
- `POYTO_DEVICE_MODEL`
- `POYTO_DEVICE_ID`
- `POYTO_VENDOR_ID`
- `POYTO_OTA_GENERATION`
- `POYTO_IS_DEVICE`

When no explicit `DeviceInfo.device_id` or `POYTO_DEVICE_ID`/`POYP_DEVICE_ID` is supplied,
Poyto generates a UUID v4 once and stores it under the APK-static app storage key
`poyp_device_id`. The same value is then reused for `X-POYP-Device-Id`, trade payloads, and
event payloads. Authentication logout clears the saved auth session but does not rotate this
device identity.

Default device-ID storage:

```text
Windows: %LOCALAPPDATA%/Poyto/device.json
Other:   $XDG_STATE_HOME/poyto/device.json
         or ~/.local/state/poyto/device.json
```

Override it with `POYTO_DEVICE_FILE` (or compatibility alias `POYP_DEVICE_FILE`). The file is
written with restrictive permissions on a best-effort basis. The official app uses platform
secure storage; Poyto reproduces the statically established generate-once/reuse lifecycle, not that mobile
storage primitive.

## Example

```powershell
$env:POYTO_TOKEN_FILE = "$HOME\\poyto-token.env"
$env:POYTO_AUTO_REFRESH = "true"
$env:POYTO_TIMEOUT = "15"
poyto profile
```

Python requires no extra wiring because `PoytoClient()` uses the same resolver:

```python
from poyto import PoytoClient

with PoytoClient() as client:
    print(client.profile())
```
