# Refresh tokens

Poyto uses POYP's Supabase Auth session model. This page deliberately separates **HAR-confirmed POYP behavior** from **documented Supabase behavior**.

## Confirmed in supplied POYP traffic

The captures show POYP using `auth.poyp.app` for Supabase Auth.

A successful Apple identity-token exchange returned:

- `access_token`
- `refresh_token`
- `token_type`
- `expires_in`
- `expires_at`
- `user`

The returned session access token was a JWT. In the latest capture its JWT `exp` exactly matched response `expires_at`, and `expires_in` was 3600 seconds. Authenticated POYP API requests then used a bearer JWT.

The returned refresh token was an **opaque string, not a JWT**. Its appearance and length must not be used as a permanent protocol contract: clients should store it exactly as returned and should not attempt to decode it.

The Apple sign-in request itself also contained a field named `access_token`. That is the Apple/provider credential, not the POYP/Supabase session access token. Poyto names it `apple_access_token` to keep the two concepts separate.

See `token-capture-findings.md` for the sanitized capture analysis.

## Not yet observed in POYP traffic

None of the supplied HARs contains a live request to:

```text
POST /auth/v1/token?grant_type=refresh_token
```

So Poyto must not claim that the exact refresh exchange has been independently captured from POYP. The implementation below is based on the standard Supabase/GoTrue Auth API used by the observed auth service.

The captures also do not reveal POYP's project-specific refresh-token reuse interval, time-boxed session lifetime, inactivity timeout, or single-session policy.

## Documented Supabase behavior

Supabase documents a session as an access-token JWT plus a unique refresh-token string. Access tokens are short-lived; one hour is the common/default JWT lifetime. Refresh tokens are used to keep a session alive without requiring another interactive sign-in. A session can still terminate because of logout, configured session limits, security-sensitive account changes, or other auth policy.

Supabase enables refresh-token rotation by default. A refresh token is normally exchanged for a new access-token + refresh-token pair, so applications should always persist the newest returned pair. Supabase also documents limited reuse/recovery exceptions for legitimate races and network failures; its documented default reuse interval is 10 seconds, but that value is configurable and the POYP capture does not prove which value POYP uses.

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

This endpoint shape is supported by Supabase's Auth API documentation. It remains marked as **Supabase-derived rather than POYP-HAR-confirmed** until a POYP capture contains an actual refresh request.

## Automatic behavior in Poyto

When `PoytoClient()` loads credentials:

- JSON session metadata uses `expires_at` directly when present;
- for a plain access-token JWT, Poyto now decodes the JWT payload locally and derives `expires_at` from `exp` when possible;
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

Never commit real tokens or HAR captures containing them. Do not print them in CI logs, issues, screenshots, examples, or documentation. If credentials may have leaked, revoke/sign out the affected session and authenticate again.
