# Refresh tokens

Poyto uses POYP's Supabase Auth session model. This page separates what was directly observed in the supplied POYP captures from behavior documented by Supabase.

## What was observed in POYP traffic

The supplied captures showed POYP using `auth.poyp.app` as its Supabase Auth/custom auth domain.

The Apple sign-in exchange returned a session containing at least:

- `access_token`
- `refresh_token`
- expiry-related fields such as `expires_in`

Authenticated POYP API requests then sent the access token as a bearer token to `api.poyp.app`.

A refresh-token exchange request itself was **not present in the supplied captures**. Poyto therefore implements refresh using the standard Supabase/GoTrue refresh-token flow rather than claiming that the exact refresh request was directly captured from POYP.

## Supabase behavior

Official Supabase documentation describes a session as an access-token JWT plus a refresh token.

Access tokens are intentionally short-lived. Supabase says they are commonly valid for roughly 5 minutes to 1 hour, with 1 hour being the normal default/recommendation for many projects.

Refresh tokens are different: they are designed to keep the session alive without forcing the user to sign in again. Supabase describes them as not expiring by time on their own, but the surrounding session can still become invalid because of logout, configured inactivity/lifetime limits, security-sensitive account changes, or session policies.

References:

- https://supabase.com/docs/guides/auth/sessions
- https://supabase.com/docs/reference/python/auth-api

## Rotation: always store the newest token

Supabase enables refresh-token rotation by default. Under rotation, a refresh token is normally exchanged once for a new access-token + refresh-token pair.

That means this is the important rule for Poyto:

> After every successful refresh, replace both the stored access token and the stored refresh token with the values returned by the auth server.

Do not keep using an older refresh token indefinitely.

Supabase provides two important protections for real-world concurrency/network failures:

1. A recently used refresh token can be accepted again during a short reuse interval. The documented default is 10 seconds.
2. In some parent-token recovery cases, Supabase can return the currently active token instead of terminating a legitimate session.

Outside those exceptions, suspicious reuse of an old refresh token can cause the session's refresh-token chain to be revoked.

References:

- https://supabase.com/docs/guides/auth/sessions#what-is-refresh-token-reuse-detection-and-what-does-it-protect-from
- https://supabase.com/docs/guides/local-development/cli/config

## Poyto refresh request

Poyto currently follows the standard Supabase token endpoint pattern:

```text
POST https://auth.poyp.app/auth/v1/token?grant_type=refresh_token
```

with a body containing the current refresh token.

The returned session replaces the in-memory session, and Poyto writes the new token pair back to its session store.

This endpoint shape is based on the Supabase Auth API behavior. Again, the supplied POYP HARs showed the auth service and refresh-token issuance, but did not contain a live POYP refresh exchange to independently confirm that exact request.

## Automatic behavior in Poyto

When `PoytoClient()` loads a stored session:

- if `expires_at` is known and the access token is expired or within 60 seconds of expiry, it refreshes immediately;
- if an authenticated POYP API request returns HTTP 401 and a refresh token exists, it refreshes once and retries the original request once;
- after a successful refresh, the newly returned access and refresh tokens are persisted;
- Poyto does not loop endlessly on repeated 401 responses.

Example:

```python
from poyto import PoytoClient

with PoytoClient() as client:
    # Saved session is loaded automatically.
    # Refresh happens automatically when needed.
    print(client.profile())
```

Manual refresh remains available:

```python
session = client.refresh()
```

## Token storage and concurrency

Because rotated refresh tokens are effectively part of a chain, two processes refreshing the same session at the same time can race each other. Supabase's reuse interval helps, but it is not a substitute for avoiding unnecessary concurrent refreshes.

For simple scripts, use one Poyto session file per account/process when possible. If multiple long-running processes must share one account, coordinate refresh operations or give each process its own independently authenticated session.

Poyto's default session file is outside the repository:

```text
Windows: %LOCALAPPDATA%/Poyto/session.json
Other:   $XDG_STATE_HOME/poyto/session.json
         or ~/.local/state/poyto/session.json
```

The path can be overridden with `POYTO_SESSION_FILE`.

## Security notes

A refresh token is more sensitive than a short-lived access token because it can be exchanged for future access tokens while the session remains valid.

Do not:

- commit it to Git;
- paste it into issues, logs, screenshots, or public chat;
- embed it in distributed source code;
- reuse an old refresh token after a successful rotation unless you are deliberately handling a recovery case.

If a refresh token may have leaked, sign out/revoke the affected session and authenticate again.

## Official references

- Supabase sessions: https://supabase.com/docs/guides/auth/sessions
- Supabase Python Auth overview: https://supabase.com/docs/reference/python/auth-api
- Supabase session configuration: https://supabase.com/docs/guides/local-development/cli/config
- Supabase OAuth refresh response/rotation guidance: https://supabase.com/docs/guides/auth/oauth-server/oauth-flows
