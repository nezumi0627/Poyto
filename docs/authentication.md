# Authentication

Poyto loads and persists POYP sessions inside the library, so callers do not need to pass a token on every run.

## Current practical login path

As of 2026-09-09, the most reliable way to bootstrap a Poyto session is to capture traffic from an account/device you are authorized to use and import the POYP authentication response from a `.har` or `.har.zip` file. Poyto extracts the returned POYP/Supabase `access_token` and `refresh_token`, saves the session outside the repository, and can then keep the session alive through refresh without another HAR capture while the refresh credential remains valid.

CLI:

```powershell
poyto login --har "capture.har.zip"
poyto profile
poyto balances
```

Python:

```python
from poyto import PoytoClient

with PoytoClient() as client:
    session = client.login_from_har("capture.har.zip")
    print(client.profile())
```

The importer only reads response bodies containing a returned session. It deliberately ignores request-body `access_token` fields because the Apple provider exchange also uses that name for a different credential.

HAR files can contain cookies, authorization headers, tokens, device identifiers, and unrelated private traffic. Keep real captures outside the repository and do not attach them to issues or CI logs.

## `token=`

The simplest Python form is:

```python
from poyto import PoytoClient

client = PoytoClient(token="YOUR_ACCESS_TOKEN")
print(client.profile())
```

`token=` accepts either a literal access token or a token file.

```python
from pathlib import Path
from poyto import PoytoClient

client = PoytoClient(token=Path("token.txt"))
client = PoytoClient(token="token.txt")
client = PoytoClient(token="@token.txt")
client = PoytoClient(token="file:token.txt")
client = PoytoClient(token_file="token.txt")
```

`POYTO_TOKEN_FILE` and the compatibility alias `POYP_TOKEN_FILE` can also point to a file.

## Supported token-file formats

### Plain access token

```text
ACCESS_TOKEN_HERE
```

### Plain access + refresh token

The first non-empty line is the access token and the second is the refresh token.

```text
ACCESS_TOKEN_HERE
REFRESH_TOKEN_HERE
```

### `.env` style

```dotenv
POYP_ACCESS_TOKEN=ACCESS_TOKEN_HERE
POYP_REFRESH_TOKEN=REFRESH_TOKEN_HERE
```

`access_token=`, `refresh_token=` and `token=` keys are also accepted where appropriate.

### JSON session

```json
{
  "access_token": "ACCESS_TOKEN_HERE",
  "refresh_token": "REFRESH_TOKEN_HERE",
  "expires_in": 3600,
  "expires_at": 1790000000,
  "token_type": "bearer"
}
```

When expiry metadata is present, automatic pre-expiry refresh can use it.

## Persist once, use automatically

```python
from poyto import PoytoClient

with PoytoClient() as client:
    client.login("ACCESS_TOKEN", "REFRESH_TOKEN")
```

A file can be persisted the same way:

```python
client.login("@token.txt")
client.login_file("token.txt")
```

After that, normal code needs no token argument:

```python
with PoytoClient() as client:
    print(client.profile())
```

CLI:

```powershell
poyto login
poyto profile
poyto balances
poyto markets
```

The CLI asks for the access token without echoing it. If you also have a refresh token:

```powershell
poyto login --refresh-token "..."
```

## Token-source priority

Poyto intentionally avoids mixing a refresh token from an unrelated saved session with an explicitly supplied access token.

The effective access-token priority is:

1. `access_token=`
2. `token=` / `token_file=`
3. `POYP_ACCESS_TOKEN`
4. `POYTO_TOKEN_FILE` / `POYP_TOKEN_FILE`
5. Poyto's saved session

An explicitly supplied `refresh_token=` can accompany the selected source.

## Apple exchange

The established POYP exchange observed in authorized traffic is:

1. Sign in with Apple produces an `id_token`, provider authorization credential, and nonce.
2. The app exchanges those values with `https://auth.poyp.app/auth/v1/token?grant_type=id_token`.
3. The response contains a Supabase access token and refresh token.
4. POYP API requests use the returned bearer token.

CLI when the Apple credentials are already available:

```powershell
poyto login-apple --id-token "..." --apple-access-token "..." --nonce "..."
```

Python:

```python
session = client.login_with_apple(
    id_token="...",
    apple_access_token="...",
    nonce="...",
)
```

Successful Apple login is persisted automatically.

### HAR-less initial Apple login

Automatically obtaining the initial Apple credentials without a capture is still **research in progress**. The main research direction is the Apple Web OAuth / Supabase authorize path, but it is not yet documented as a dependable POYP login flow.

Until that is established, importing the authentication response from authorized POYP traffic is the reliable bootstrap method. Once a refresh token has been persisted, normal refresh can maintain the session without repeated HAR capture.

## Automatic refresh

If a saved/file/HAR session contains both `expires_at` and a refresh token, `PoytoClient()` refreshes it when it is expired or within 60 seconds of expiry. If an authenticated API request later returns HTTP 401, Poyto refreshes once and retries the original request once when a refresh token is available.

Manual refresh still works:

```python
client.refresh()
```

The POYP refresh exchange used by Poyto was live-verified on 2026-09-09 with an existing authorized refresh token. Refresh-token rotation and remaining unknown policy details are documented in [Refresh tokens](refresh-tokens.md).

## Session location

Poyto does not write credentials into the repository or current working directory by default.

- Windows: `%LOCALAPPDATA%/Poyto/session.json`
- Linux/macOS-style environments: `$XDG_STATE_HOME/poyto/session.json` or `~/.local/state/poyto/session.json`
- Override: `POYTO_SESSION_FILE=/custom/path/session.json`

On POSIX systems Poyto attempts to set the session file to mode `0600`.

## Logout

```powershell
poyto logout
```

This performs the supported server logout when a session is available and clears Poyto's local saved session. To only remove the local file:

```powershell
poyto logout --local-only
```

Never commit access tokens, refresh tokens, Apple identity tokens, cookies, private traffic exports, or stable device identifiers.
