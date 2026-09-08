# Authentication

Poyto loads and persists POYP sessions inside the library, so callers do not need to pass a token on every run.

## Recommended flow

First login once:

```powershell
poyto login
```

The CLI asks for the access token without echoing it. If you also have a refresh token:

```powershell
poyto login --refresh-token "..."
```

After that, normal commands load the saved session automatically:

```powershell
poyto profile
poyto balances
poyto markets
```

Python works the same way:

```python
from poyto import PoytoClient

with PoytoClient() as client:
    print(client.profile())
```

For an existing token from your own code:

```python
from poyto import PoytoClient

with PoytoClient() as client:
    client.login(access_token, refresh_token)
    print(client.profile())
```

`login()` saves the session by default. The next `PoytoClient()` automatically reads it.

## Apple exchange

The observed POYP flow is:

1. Sign in with Apple produces an `id_token` and, in the observed capture, an Apple access token and nonce.
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

If the saved session contains both `expires_at` and a refresh token, `PoytoClient()` refreshes it when it is expired or within 60 seconds of expiry, then writes the new session back to disk.

Manual refresh still works:

```python
client.refresh()
```

## Session location

Poyto does not write credentials into the repository or current working directory by default.

- Windows: `%LOCALAPPDATA%/Poyto/session.json`
- Linux/macOS-style environments: `$XDG_STATE_HOME/poyto/session.json` or `~/.local/state/poyto/session.json`
- Override: `POYTO_SESSION_FILE=/custom/path/session.json`

On POSIX systems Poyto attempts to set the session file to mode `0600`.

For environments that already provide secrets, explicit constructor arguments and `POYP_ACCESS_TOKEN` / `POYP_REFRESH_TOKEN` still take precedence over the saved session.

## Logout

```powershell
poyto logout
```

This performs the observed server logout when a session is available and clears Poyto's local saved session. To only remove the local file:

```powershell
poyto logout --local-only
```

Never commit access tokens, refresh tokens, Apple identity tokens, cookies, HAR files, or stable device identifiers.
