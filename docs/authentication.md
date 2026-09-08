# Authentication

Poyto loads and persists POYP sessions inside the library, so callers do not need to pass a token on every run.

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

The established POYP flow is:

1. Sign in with Apple produces an `id_token`, Apple access token, and nonce as required by the provider flow.
2. The app exchanges those values with `https://auth.poyp.app/auth/v1/token?grant_type=id_token`.
3. The response contains a Supabase access token and usually a refresh token.
4. POYP API requests use the resulting bearer token.

CLI:

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

## Automatic refresh

If a saved/file session contains both `expires_at` and a refresh token, `PoytoClient()` refreshes it when it is expired or within 60 seconds of expiry. If an authenticated API request later returns HTTP 401, Poyto refreshes once and retries the original request once when a refresh token is available.

Manual refresh still works:

```python
client.refresh()
```

Refresh-token rotation and the distinction between established POYP behavior and standard Supabase behavior are documented in [Refresh tokens](refresh-tokens.md).

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
