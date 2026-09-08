# Authentication

Poyto supports the authentication flow observed in the supplied POYP HAR captures.

## Observed flow

1. Sign in with Apple produces an `id_token` and, in the observed capture, an Apple access token and nonce.
2. The app exchanges those values with `https://auth.poyp.app/auth/v1/token?grant_type=id_token`.
3. The response contains a Supabase `access_token` and usually a `refresh_token`.
4. POYP API requests use `Authorization: Bearer <access_token>` against `https://api.poyp.app`.

## Existing session

```powershell
$env:POYP_ACCESS_TOKEN="..."
$env:POYP_REFRESH_TOKEN="..."
poyto profile
```

Python:

```python
from poyto import PoytoClient

with PoytoClient.from_env() as client:
    print(client.profile())
```

## Apple exchange

```powershell
$env:POYP_APPLE_ID_TOKEN="..."
$env:POYP_APPLE_ACCESS_TOKEN="..."
$env:POYP_APPLE_NONCE="..."
poyto login-apple
```

Python:

```python
session = client.login_with_apple(
    id_token="...",
    apple_access_token="...",
    nonce="...",
)
```

## Refresh

```python
session = client.refresh()
```

The CLI masks returned secrets. Never commit access tokens, refresh tokens, Apple identity tokens, cookies, HAR files, or stable device identifiers.

## Supabase key

The client contains the publishable Supabase key observed in public client traffic. It is not a user's bearer token. Override it with `POYP_SUPABASE_KEY` if POYP changes the client configuration.
