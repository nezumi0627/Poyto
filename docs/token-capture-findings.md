# Token behavior notes

This document records token properties that are sufficiently established for the current Poyto implementation. Secret values are intentionally omitted.

## Authentication service

POYP uses `https://auth.poyp.app` for Supabase Auth and `https://api.poyp.app` for its application API.

The Apple sign-in exchange uses:

```text
POST /auth/v1/token?grant_type=id_token
```

The request carries the public Supabase publishable key and includes provider credentials required by the Apple sign-in flow. Relevant fields include:

```text
provider
id_token
access_token
nonce
gotrue_meta_security
```

The `access_token` field in this request is the Apple/provider credential used during the identity exchange; it is **not** the POYP/Supabase session access token returned by the response.

A successful response includes:

```text
access_token
refresh_token
token_type
expires_in
expires_at
user
```

## Session access token

The returned POYP/Supabase `access_token` is a JWT. Authenticated requests to `api.poyp.app` use it as:

```text
Authorization: Bearer <access-token>
```

A known successful session used a 3600-second access-token lifetime, and the JWT `exp` claim matched `expires_at`. That value should not be treated as a permanent guarantee.

## Refresh token

The returned `refresh_token` is an opaque secret, not a JWT. Poyto must not assume refresh tokens begin with `eyJ`, contain claims, or can be decoded as JWTs.

The refresh token should be stored and returned exactly as issued.

## Important distinction: two different `access_token` fields

The Apple token-exchange request and the Supabase session response both contain a field named `access_token`, but they have different roles:

1. request `access_token`: Apple/provider credential participating in Apple sign-in;
2. response `access_token`: POYP/Supabase bearer JWT used for authenticated POYP API requests.

Poyto calls the first one `apple_access_token` in its Python API to avoid mixing them up.

## Refresh exchange boundary

The exact POYP refresh exchange is not directly established. Poyto's refresh implementation follows the documented Supabase/GoTrue endpoint for the same authentication service, but documentation must keep that behavior labeled **implemented/inferred** rather than guaranteed POYP behavior.

Likewise, Poyto does not claim POYP's project-specific refresh-token reuse interval, session lifetime policy, inactivity timeout, or single-session policy. Supabase documents defaults and behavior, but those settings are configurable by the project owner.

## Implementation rules derived from the evidence

Poyto follows these rules:

- access tokens may be inspected as JWTs only to obtain local metadata such as `exp`; decoding claims is not signature verification;
- refresh tokens are always treated as opaque strings;
- a refresh token is never inferred from an access token;
- if a JWT `exp` is available, Poyto can proactively refresh before expiry even when a token was loaded from plain text;
- successful refresh responses replace the complete stored token pair;
- real credentials and private traffic exports are never committed to the repository, examples, tests, or documentation.

See also `refresh-tokens.md` for the distinction between established POYP behavior and documented Supabase behavior.
