# Token findings from the 2026-09-08 capture

This document records only token properties that were directly observable in the supplied POYP HAR. Secret values are intentionally omitted.

## Confirmed from the capture

POYP used `https://auth.poyp.app` for Supabase Auth and `https://api.poyp.app` for its application API.

The Apple sign-in exchange was:

```text
POST /auth/v1/token?grant_type=id_token
```

The request carried the public Supabase publishable key in both `apikey` and `Authorization: Bearer <publishable-key>`. Its JSON body contained:

```text
provider
id_token
access_token
nonce
gotrue_meta_security
```

For this capture, `provider` was `apple`. The `access_token` field in this request is the Apple/provider credential used during the identity exchange; it is **not** the POYP/Supabase session access token returned by the response.

The successful response contained:

```text
access_token
refresh_token
token_type
expires_in
expires_at
user
```

### Session access token

The returned POYP/Supabase `access_token` was a JWT: three dot-separated Base64URL sections and an `eyJ...` prefix. Its claims showed an authenticated Supabase session. The response reported `token_type = bearer`.

The captured session had a 3600-second access-token lifetime, and the JWT `exp` claim matched the response `expires_at`. This is direct evidence for that captured session, not a promise that POYP can never change its configured JWT lifetime.

Authenticated requests to `api.poyp.app` used a POYP/Supabase session access token as:

```text
Authorization: Bearer <access-token>
```

### Refresh token

The returned `refresh_token` was an opaque string, not a JWT. In this capture it was short and contained no JWT dot separators. Therefore Poyto must **not** assume that refresh tokens begin with `eyJ`, contain claims, or can be decoded as JWTs.

The refresh token should be treated as an opaque secret and passed back exactly as issued.

## Important distinction: two different `access_token` fields

The Apple token-exchange request and the Supabase session response both contain a field named `access_token`, but they have different roles:

1. request `access_token`: Apple/provider credential participating in Apple sign-in;
2. response `access_token`: POYP/Supabase bearer JWT used for authenticated POYP API requests.

Poyto calls the first one `apple_access_token` in its Python API to avoid mixing them up.

## What this capture did NOT confirm

There was no request using:

```text
POST /auth/v1/token?grant_type=refresh_token
```

in this HAR. Therefore the exact POYP refresh exchange remains unobserved in supplied traffic. Poyto's refresh implementation follows the documented Supabase/GoTrue endpoint for the same auth service, but docs must not label that request as HAR-confirmed until a capture actually contains it.

Likewise, the capture cannot prove POYP's project-specific refresh-token reuse interval, session lifetime policy, or single-session policy. Supabase documents defaults and behavior, but those settings are configurable by the project owner.

## Implementation rules derived from the evidence

Poyto follows these rules:

- access tokens may be inspected as JWTs only to obtain local metadata such as `exp`; decoding claims is not signature verification;
- refresh tokens are always opaque strings;
- a refresh token is never inferred from an access token;
- if a JWT `exp` is available, Poyto can proactively refresh before expiry even when a token was loaded from plain text;
- successful refresh responses replace the complete stored token pair;
- credentials from HAR files are never committed to the repository, examples, tests, or documentation.

See also `refresh-tokens.md` for the distinction between captured POYP behavior and documented Supabase behavior.
