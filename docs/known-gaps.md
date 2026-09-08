# Known gaps and unverified behavior

This file is the canonical **do-not-claim** list for Poyto.

If a behavior is listed here, the project either lacks sufficient POYP evidence for it, has only partial evidence, or intentionally does not implement it. New evidence should move an item out of this file only after the request/response shape is established or independently documented and covered by tests.

## Authentication gaps

### Refresh-token exchange is not directly established

Poyto implements the standard Supabase/GoTrue-style refresh exchange because the authentication backend is Supabase-based and issues refresh tokens. The exact POYP refresh request/response behavior is still treated as **inferred**, not guaranteed.

Unknown details include:

- whether POYP changes the standard request shape
- exact refresh-token reuse/rotation behavior in this project
- project-specific refresh-token invalidation policy
- server behavior after simultaneous refreshes
- exact error bodies for expired/revoked refresh tokens

### Apple login prerequisites are only partially generalized

A successful Apple-to-POYP id-token exchange is established. That does not prove every possible Apple login variant, nonce policy, account state, or migration path.

Unknown or unverified:

- every Apple authorization error response
- first-ever signup edge cases
- account deletion/recreation behavior
- account-linking behavior
- non-Apple authentication providers
- MFA or recovery flows

## Ad reward gaps

A successful `watch_ad` claim and response shape are established. What remains unknown is the server-side eligibility logic.

Poyto does **not** claim knowledge of:

- how POYP proves an advertisement was legitimately completed
- whether proof is held server-side, in an SDK callback, in transient session state, or elsewhere
- cooldown timing
- whether a previously seen reward value is fixed
- whether a previously seen daily limit is fixed globally
- regional/account/experiment-specific reward values
- failure response schemas for early, duplicate, ineligible, expired, or rate-limited claims
- whether multiple ad providers use different `source` values
- anti-abuse or fraud-detection rules

Poyto does not fabricate Google Mobile Ads callbacks, rewarded-video completion events, or third-party ad-network proof.

## Trading gaps

Buy and sell request shapes are established, but the project does not have enough evidence to claim complete knowledge of the trading engine.

Unknown or unverified:

- price-formation formula
- spread/slippage semantics
- exact share/point rounding rules
- minimum and maximum order sizes in every market state
- idempotency guarantees for `requestId`
- duplicate-order handling
- settlement implementation
- cancellation/undo support
- limit orders
- partial fills
- market-maker behavior
- fee rules
- every trade error code/body
- behavior during suspended, resolved, or rapidly transitioning markets

Do not add guessed trading endpoints or formulas to the public client.

## Market gaps

Supported read routes do not imply complete market administration support.

No sufficient evidence currently backs client methods for:

- creating markets
- editing markets
- deleting markets
- resolving markets
- cancelling markets
- administrative moderation
- changing market outcomes
- privileged/internal market controls

The exact semantics of every `feed`, `phase`, `sort`, chart timeframe, and auxiliary field are also not fully documented.

## Comment and social gaps

Not established or insufficiently supported:

- unlike-comment endpoint
- comment reactions other than the supported like action
- editing/deleting another user's content
- reporting users/comments
- blocking/unblocking writes
- direct/private messaging
- posting to global chat
- realtime chat/socket protocol
- moderation/admin actions
- notification preference writes

`GET /api/me/blocked-users` is supported; a corresponding block/unblock write route has not been established.

## Referral gaps

Supported referral reads and referral-code update do not establish:

- all code validation rules
- reward calculation rules
- referral payout schedule
- anti-abuse rules
- retroactive code assignment behavior
- administrator/referral campaign controls

## Mission, streak, campaign and gacha gaps

Read/status endpoints exist, but there is insufficient evidence for arbitrary mutation endpoints.

Do not assume methods for:

- completing a mission manually
- forcing a login streak
- claiming campaign rewards without established request evidence
- triggering loss gacha
- changing campaign result state

Server responses may themselves encode claimability; that is not equivalent to a supported write route.

## Notification gaps

Supported:

- notification list
- unread count
- read-all
- push-token registration

Not sufficiently evidenced:

- single-notification read endpoint
- deleting notifications
- notification preferences
- push-token deletion/revocation route
- platform-specific push payload schema

## Walking challenge gaps

Only status retrieval is sufficiently established.

Unknown:

- step submission route
- health-data synchronization
- reward-claim route
- anti-cheat rules
- reset schedule

## Discovery/search gaps

Supported discovery routes do not prove:

- arbitrary full-text search request parameters
- write/customization endpoints for home tabs/sections
- interest subscription writes
- every onboarding mutation

## Event telemetry gaps

`POST /api/events` is supported, but a generic wrapper does not mean the event schema is fully understood.

Unknown:

- complete event-name catalog
- required properties for every event
- whether events influence rewards, ranking, personalization, or anti-abuse systems
- retry/idempotency behavior

Do not invent event payloads and present them as official.

## Provider rewards gaps

The provider-rewards read route is supported with a source such as `skyflag`, but this does not establish integration APIs for arbitrary providers.

Unknown:

- supported provider list
- provider callback endpoints
- offer completion verification
- payout rules
- webhook/signature formats

## Realtime and transport gaps

Poyto currently focuses on HTTP APIs. There is no sufficiently backed implementation for:

- WebSocket realtime feeds
- server-sent events
- push-notification decryption/processing
- background mobile session behavior
- official offline synchronization protocol

## Device identity and headers

Requests use `x-poyp-*` device/application metadata. Poyto can send configurable equivalents, but does not claim to know which fields are mandatory in every context or how server-side device trust is calculated.

Unknown:

- device attestation
- jailbreak/root detection interaction
- device-ban logic
- stable-device enrollment rules
- exact OTA-generation semantics

## Rate limits and anti-abuse

No complete rate-limit specification is established.

Poyto does not claim:

- request-per-minute limits
- per-route quotas
- retry-after rules for every endpoint
- anti-bot thresholds
- fraud scoring behavior
- account restriction rules

## Response schemas

Most public methods intentionally return server JSON rather than pretending every response is completely modeled. Only fields with enough value and evidence should receive dedicated TypedDict/dataclass models.

A successful response sample does not prove:

- all optional fields
- all error variants
- future backwards compatibility
- field availability across accounts/app versions/experiments

## API stability

POYP's API is undocumented and unofficial from Poyto's perspective. Routes, parameters, headers, response shapes, and authentication behavior can change at any time.

There is no official compatibility guarantee.

## Evidence coverage limitations

Current documentation reflects only behavior that has been sufficiently established. Absence from the current evidence set means **unknown**, not necessarily nonexistent.

## Rules for resolving a gap

Before moving an item from unknown to supported:

1. Establish or independently document the real request.
2. Verify host, method, path, query, body, and relevant headers.
3. When possible, verify a successful response and at least one failure case.
4. Sanitize all tokens, user IDs, device IDs, cookies, Apple credentials, and other private values.
5. Add an exact `httpx.MockTransport` regression test.
6. Update `docs/endpoints.md`, `docs/capabilities.md`, and this file.
7. Never fill evidence gaps with guessed routes merely because a naming pattern looks plausible.
