# Refresh tokens

Poyto uses POYP's Supabase Auth session model. This page deliberately separates **established POYP behavior** from **documented Supabase behavior**.

## Established POYP behavior

POYP uses `auth.poyp.app` for Supabase Auth.

A successful Apple identity-token exchange returns:

- `access_token`
- `refresh_token`
- `token_type`
- `expires_in`
- `expires_at`
- `user`

The session access token is a JWT and authenticated POYP API requests use it as a bearer token. The observed access-token lifetime for a known session was 3600 seconds, but clients should not assume that lifetime can never change.

The returned refresh token is an **opaque string, not a JWT**. Its appearance and length must not be used as a permanent protocol contract: clients should store it exactly as returned and should not attempt to decode it.

The Apple sign-in request itself also contains a field named `access_token`. That is the Apple/provider credential, not the POYP/Supabase session access token. Poyto names it `apple_access_token` to keep the two concepts separate.

See `token-capture-findings.md` for sanitized token-behavior notes.

## Inferred POYP refresh behavior

The exact POYP refresh exchange is not directly established, so Poyto does not present it as guaranteed POYP behavior. The implementation follows the standard Supabase/GoTrue Auth API used by the authentication service.

Poyto also does not claim to know POYP's project-specific refresh-token reuse interval, time-boxed session lifetime, inactivity timeout, or single-session policy.

## Documented Supabase behavior

Supabase documents a session as an access-token JWT plus a unique refresh-token string. Access tokens are short-lived; refresh tokens keep a session alive without requiring another interactive sign-in. A session can still terminate because of logout, configured session limits, security-sensitive account changes, or other auth policy.

Supabase enables refresh-token rotation by default. A refresh token is normally exchanged for a new access-token + refresh-token pair, so applications should always persist the newest returned pair. Supabase also documents limited reuse/recovery exceptions for legitimate races and network failures; its default reuse interval is documented as 10 seconds, but that value is configurable and should not be assumed to match POYP.

Official references:

- https://supabase.com/docs/guides/auth/sessions
- https://supabase.com/docs/reference/python/auth-api
- https://supabase.com/docs/guides/local-development/cli/config
- https://supabase.com/docs/reference/self-hosting-auth

## Poyto refresh implementation

Poyto follows the standard GoTrue endpoint shape:

```text
POST https://auth.poyp.app/auth/v1/token?grant_type=refresh_token
Content-Type: application/json

{"refresh_token": "<opaque refresh token>"}
```

The returned session replaces the in-memory session and, when persistence is enabled, the newly returned access and refresh tokens replace the stored pair.

This endpoint shape is supported by Supabase's Auth API documentation. It remains marked as **implemented/inferred** until exact POYP refresh behavior is independently established.

## Automatic behavior in Poyto

When `PoytoClient()` loads credentials:

- JSON session metadata uses `expires_at` directly when present;
- for a plain access-token JWT, Poyto decodes the JWT payload locally and derives `expires_at` from `exp` when possible;
- JWT decoding is only metadata inspection and does **not** mean the signature was verified locally;
- if expiry is known and the access token is expired or within 60 seconds of expiry, Poyto refreshes when a refresh token is available;
- if an authenticated POYP API request returns HTTP 401 and a refresh token exists, Poyto refreshes once and retries once;
- after a successful refresh, the newest token pair is persisted;
- Poyto never attempts to decode a refresh token as a JWT.

Example:

```python
from poyto import PoytoClient

with PoytoClient() as client:
    print(client.profile())
```

Manual refresh remains available:

```python
session = client.refresh()
```

## Token storage and concurrency

With rotation, two processes refreshing the same session can race. Supabase has reuse/recovery behavior for legitimate races, but applications should not rely on it as a locking mechanism. Prefer one active session store per independently authenticated client/process when possible.

Poyto's default session file is outside the repository:

```text
Windows: %LOCALAPPDATA%/Poyto/session.json
Other:   $XDG_STATE_HOME/poyto/session.json
         or ~/.local/state/poyto/session.json
```

Override it with `POYTO_SESSION_FILE` when necessary.

## Security

Both token types are credentials. A refresh token is particularly sensitive because it can mint future access tokens while its session remains valid.

Never commit real tokens or private traffic exports containing them. Do not print them in CI logs, issues, screenshots, examples, or documentation. If credentials may have leaked, revoke/sign out the affected session and authenticate again.
