# Capability inventory

This document is the canonical inventory of what Poyto can do today and how strong the evidence is for each behavior.

Poyto is reconstructed from authorized POYP traffic. A method existing in the codebase does **not** automatically mean the corresponding server behavior is fully proven. Every capability below is therefore tagged by evidence level.

## Evidence levels

| Level | Meaning |
| --- | --- |
| **Observed** | The request shape was directly present in supplied POYP HAR traffic. |
| **Observed success** | The request and a successful server response were both captured. |
| **Implemented / inferred** | Poyto implements the behavior, but the exact request was not directly present in the supplied POYP HARs. |
| **Unknown** | No sufficient capture or independent documentation exists. Poyto must not invent behavior. |

## Code-size snapshot

The source LOC snapshot is computed from `src/poyto/**/*.py` using `python scripts/code_stats.py`.

The script reports both physical lines and non-blank lines and also separates core code, resource wrappers, and tests. The CI job runs the same script on Python 3.14 so the documented measurement is reproducible instead of being manually estimated.

> The numeric snapshot is updated from CI output when this document changes. If the tree has moved since the last snapshot, run `python scripts/code_stats.py` and treat its output as authoritative.

## Authentication and session lifecycle

| Capability | Public surface | Evidence |
| --- | --- | --- |
| Use an existing POYP access token | `PoytoClient(token=...)`, `POYTO_TOKEN` | Implemented; authenticated HAR requests directly observed |
| Read token from plaintext / dotenv / JSON | token loader | Local library feature |
| Save and reload a session | `poyto login`, `SessionStore` | Local library feature |
| Apple id-token login | `login_with_apple()`, `poyto login-apple` | **Observed success**: `POST /auth/v1/token?grant_type=id_token` |
| Store access + refresh pair returned by login | `AuthSession`, `SessionStore` | **Observed success** for issuance |
| Refresh shortly before expiry | automatic client lifecycle | **Implemented / inferred** |
| Refresh after one authenticated HTTP 401 and retry once | automatic client lifecycle | Local policy; refresh exchange itself inferred |
| Refresh-token rotation persistence | automatic client lifecycle | **Implemented / inferred** from standard Supabase/GoTrue behavior |
| Remote logout | `logout(local_only=False)` | **Observed**: `POST /auth/v1/logout?scope=global` |
| Local-only logout | `logout(local_only=True)` | Local library feature |
| Inspect session metadata without printing secrets | `session_info()`, `token_kind()` | Local library feature |

Important limitation: the supplied POYP HARs show refresh-token **issuance**, but no POYP `grant_type=refresh_token` exchange was captured. See `refresh-tokens.md`.

## Account and balances

The following request families are implemented and directly observed unless marked otherwise:

- profile
- balances
- portfolio
- portfolio history
- balance history
- balance transactions
- expiring balances
- missions
- login streak
- campaign results
- provider rewards
- loss-gacha status
- notifications
- unread notification count
- mark all notifications read
- push-token registration
- blocked users
- walking-challenge status

Python surfaces live primarily in `resources/account.py`; CLI exposes the common read operations plus selected writes.

## Ad rewards

`claim_ad_reward(source="watch_ad")` is a first-class library operation.

Directly observed request:

```text
POST /api/me/ad-rewards/claim?source=watch_ad
```

No JSON body was present in the captured request.

A newer supplied HAR captured **HTTP 200 success** with these response fields:

- `earnId`
- `rewardPoints`
- `pointBalanceAfter`
- `dailyViewCount`
- `dailyViewLimit`

`AdRewardClaimResponse` types those observed fields. One capture returned 5 reward points and a daily count of 2/5; those values are observations, not universal constants.

CLI surface:

```text
poyto claim-ad-reward --yes
```

Poyto does not fabricate ad-completion callbacks, SDK events, reward proofs, or eligibility state.

## Referral

Implemented and observed:

- read referral code
- read referral stats
- check referral-code availability
- update referral code

The update operation is state-changing and CLI use requires `--yes`.

## Markets and pricing

Implemented and observed:

- list markets with feed/phase/sort/limit parameters
- read one market
- related markets
- screen auxiliary data
- current-user positions for a market
- market activity
- multi-market chart data
- asset price route (`/api/prices/{asset}`)
- iterator helper for market pagination

The helper pagination policy is library-side convenience; server cursor behavior is only assumed where matching cursor fields were observed.

## Trading

Implemented and observed:

- buy
- sell

Observed buy fields include `marketId`, `positionIndex`, `pointAmount`, `orderSurface`, `requestId`, `displayPreset`, `entryPoint`, `sessionId`, and `deviceId`.

Observed sell fields include `marketId`, `positionIndex`, `shares`, `orderSurface`, `entryPoint`, `sessionId`, and `deviceId`.

CLI buy/sell operations require `--yes`.

Poyto does not claim to know undocumented server-side validation, market settlement rules, slippage behavior, pricing formulas, anti-abuse rules, or idempotency semantics beyond what captures show.

## Comments and social actions

Implemented and observed:

- comment moderation status
- create a market comment
- create a reply using `parentCommentId`
- edit a comment
- delete a comment
- like a comment
- follow a user
- unfollow a user
- user profile
- follow status
- team follows
- followers
- following
- user balance history
- user portfolio history

Not observed: unlike-comment request. Poyto therefore does not invent an unlike endpoint.

## Discovery and home

Implemented and observed:

- home sections
- home tabs
- search sections
- interest subcategories
- campaign banners
- onboarding data

## Timeline, rankings, chat and events

Implemented request wrappers exist for captured traffic covering:

- global-chat messages
- trader leaderboard
- recent trades
- recent comments
- rising markets
- followed-trades timeline
- generic event submission

These are HTTP wrappers around observed routes. Poyto does not claim realtime socket support, message sending support, moderation-control support, or an official event schema unless separately captured.

## Raw HTTP escape hatch

`PoytoClient.request(...)` and the CLI `raw` command can call an explicit path supplied by the caller. This is an escape hatch, not evidence that arbitrary POYP endpoints are supported.

The raw API intentionally does not turn guesses into documented capabilities.

## CLI capabilities

Common commands include:

- authentication: `login`, `login-apple`, `logout`, `refresh`
- account: `profile`, `balances`, `portfolio`, `missions`, `streak`, `notifications`, `walking`
- discovery: `home`
- referral: `referral`, `referral-available`, `set-referral`
- markets: `markets`, `market`, `activity`, `charts`, `price`
- transactions: `transactions`, `buy`, `sell`
- social: `comment`, `edit-comment`, `delete-comment`, `like-comment`, `follow`, `unfollow`, `user`
- account writes: `read-all-notifications`, `claim-ad-reward`
- debugging/advanced: `raw`

State-changing CLI commands require `--yes` where implemented by the parser/dispatcher.

## Local reliability features

Poyto also provides behavior that is independent of undocumented POYP semantics:

- explicit credential-source priority
- environment-variable configuration
- token-file parsing
- configurable API/auth base URLs
- configurable timeout
- reusable device metadata headers
- context-manager support
- typed package marker (`py.typed`)
- normalized API exceptions
- secret-masked session inspection
- pytest mock transports for request-shape regression tests
- Ruff, mypy and package-build CI
- Python 3.10 through 3.14 CI matrix

## What “supported” means here

A supported method means Poyto has a maintained client surface and tests for the request shape or local behavior. It does not mean POYP guarantees the endpoint, that every possible response is modeled, or that the route will remain stable.

For the inverse list—things Poyto deliberately does not claim because evidence is absent—see `known-gaps.md`.
