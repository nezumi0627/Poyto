# Capability inventory

This is the canonical inventory of what Poyto can do today, how much code implements it, and how strong the evidence is.

A method existing in the codebase does **not** automatically mean the server behavior is fully proven. Poyto separates established behavior from inferred and unknown behavior.

## Evidence levels

| Level | Meaning |
| --- | --- |
| **Observed** | The real request shape is backed by direct POYP request/response evidence. |
| **Observed success** | The request and a successful server response are both established. |
| **Implemented / inferred** | Poyto implements the behavior, but exact POYP behavior is not directly established. |
| **Unknown** | There is not enough evidence or independent documentation. Do not invent behavior. |

## Exact code-size snapshot

Measured by CI with `python scripts/code_stats.py`:

| Area | Files | Physical lines | Non-blank lines |
| --- | ---: | ---: | ---: |
| Core/MCP source outside `resources/` | 20 | 2,004 | 1,705 |
| Resource wrappers `src/poyto/resources/*.py` | 7 | 482 | 396 |
| **Source total** | **27** | **2,486** | **2,101** |
| Tests | 9 | 1,107 | 886 |

Per-source-file snapshot:

| File | Lines | Non-blank | Main responsibility |
| --- | ---: | ---: | --- |
| `src/poyto/_http.py` | 195 | 171 | HTTP transport, headers, auth exchange/refresh/logout |
| `src/poyto/mcp/server.py` | 329 | 289 | FastMCP server and POYP tools |
| `src/poyto/auto.py` | 219 | 197 | credential loading, persistence, auto-refresh, 401 retry |
| `src/poyto/cli_dispatch.py` | 192 | 179 | CLI command execution |
| `src/poyto/token_loader.py` | 163 | 136 | token/text/file parsing |
| `src/poyto/resources/account.py` | 144 | 113 | account, balances, notifications, referral and claims |
| `src/poyto/cli_parser.py` | 135 | 107 | CLI arguments and command definitions |
| `src/poyto/resources/social.py` | 129 | 107 | users, follows, comments/social reads/writes |
| `src/poyto/har_loader.py` | 111 | 92 | secret-aware HAR/HAR.zip session import |
| `src/poyto/models.py` | 101 | 80 | typed structures |
| `src/poyto/session_store.py` | 98 | 82 | persistent local session storage |
| `src/poyto/config.py` | 86 | 71 | environment/settings/device configuration |
| `src/poyto/mcp/config.py` | 76 | 64 | MCP environment/CLI settings |
| `src/poyto/resources/markets.py` | 74 | 61 | markets, positions, activity, charts, prices |
| `src/poyto/_resource.py` | 65 | 53 | shared resource helpers/pagination helpers |
| `src/poyto/resources/trades.py` | 60 | 55 | buy/sell request wrappers |
| `src/poyto/__init__.py` | 49 | 46 | public exports and compatibility aliases |
| `src/poyto/token_info.py` | 43 | 32 | secret-safe token/session inspection |
| `src/poyto/resources/events.py` | 35 | 30 | event/timeline/ranking/chat wrappers |
| `src/poyto/exceptions.py` | 34 | 24 | normalized exceptions |
| `src/poyto/client.py` | 31 | 25 | low-level client composition |
| `src/poyto/cli.py` | 28 | 22 | CLI entrypoint/output |
| `src/poyto/mcp/__main__.py` | 26 | 18 | MCP entrypoint |
| `src/poyto/resources/discovery.py` | 25 | 16 | home/search/discovery wrappers |
| `src/poyto/mcp_server.py` | 20 | 15 | legacy MCP compatibility shim |
| `src/poyto/resources/__init__.py` | 15 | 14 | resource exports |
| `src/poyto/mcp/__init__.py` | 3 | 2 | MCP package exports |

These values are a snapshot, not a marketing metric. `python scripts/code_stats.py` is authoritative after the tree changes.

## Authentication and session lifecycle

| Capability | Public surface | Evidence |
| --- | --- | --- |
| Use existing access token | `PoytoClient(token=...)`, env/token file | Implemented; authenticated behavior established |
| Plaintext/dotenv/JSON token files | token loader | Local feature |
| Save/reload session | `poyto login`, `SessionStore` | Local feature |
| Apple id-token login | `login_with_apple()`, `login-apple` | **Observed success** |
| Receive/store access + refresh pair | `AuthSession`, `SessionStore` | **Observed success** for issuance |
| Refresh shortly before expiry | automatic lifecycle | **Implemented / inferred** |
| One refresh + retry after authenticated 401 | automatic lifecycle | Local policy; exchange inferred |
| Persist rotated refresh pair | automatic lifecycle | **Implemented / inferred** |
| Remote global logout | `logout(local_only=False)` | **Observed** |
| Local-only logout | `logout(local_only=True)` | Local feature |
| Inspect token/session shape without leaking secrets | `session_info()`, `token_kind()` | Local feature |

Critical boundary: refresh-token issuance is established, while the exact POYP refresh exchange is not. The refresh request follows standard Supabase/GoTrue behavior and remains inferred.

## Account, balances and notifications

Implemented wrappers cover profile, balances, portfolio, portfolio history, balance history, balance transactions, expiring balances, missions, login streak, campaign results, provider rewards, loss-gacha status, notifications, unread count, read-all, push-token registration, blocked users, referral data and walking-challenge status.

Primary implementation footprint: `resources/account.py` (144 lines), plus transport/session infrastructure.

## Ad rewards

`claim_ad_reward(source="watch_ad")` is a first-class operation.

Established request:

```text
POST /api/me/ad-rewards/claim?source=watch_ad
```

No JSON body is required by the established request shape. A successful response includes:

- `earnId`
- `rewardPoints`
- `pointBalanceAfter`
- `dailyViewCount`
- `dailyViewLimit`

`AdRewardClaimResponse` types those fields. Reward values and daily limits are treated as server-provided values rather than universal constants. Poyto does not fabricate ad-SDK completion callbacks, proof, eligibility state, or anti-abuse state.

## Markets and pricing

Implemented and observed: list markets, market detail, related markets, screen auxiliary data, current-user positions, market activity, multi-market charts, asset prices, and library-side pagination helpers.

Primary implementation: `resources/markets.py` (74 lines).

## Trading

Implemented and observed: buy and sell.

Primary implementation: `resources/trades.py` (60 lines), with shared transport/session/device handling elsewhere.

Supported buy fields include `marketId`, `positionIndex`, `pointAmount`, `orderSurface`, `requestId`, `displayPreset`, `entryPoint`, `sessionId`, and `deviceId`.

Supported sell fields include `marketId`, `positionIndex`, `shares`, `orderSurface`, `entryPoint`, `sessionId`, and `deviceId`.

Poyto does not claim complete knowledge of settlement, pricing formulas, slippage, fees, idempotency, anti-abuse, or every error response.

## Settlement claims

`claim_settlement(market_id, position_index)` is **Implemented / inferred**. The APK static
inventory independently shows `POST /api/settlements/claim`, while the current JSON shape
`{"marketId": ..., "positionIndex": ...}` comes from the contributed implementation and is
covered by offline request-shape tests. This repository does not yet contain independent live
request/response evidence proving that body or a successful response.

The CLI command `settlement-claim` requires `--yes`, and the MCP tool `settlement_claim`
requires `confirm=true`. Claim eligibility, payout semantics, response fields and the other APK
settlement routes remain unverified.

## Comments and social

Implemented/observed surfaces include moderation status, comment/reply creation, edit, delete, like, follow/unfollow, user profile, follow status, team follows, followers/following, user balance history and user portfolio history.

Primary implementation: `resources/social.py` (129 lines).

Unlike-comment is not established and is intentionally not invented.

## Discovery, rankings, timeline, chat reads and events

Supported wrappers cover home sections/tabs, search sections, interest subcategories, campaign banners, onboarding, global-chat messages, leaderboards, recent trades/comments, rising markets, followed-trades timeline and generic event submission.

Primary implementation: `resources/discovery.py` (25 lines) + `resources/events.py` (35 lines).

This does not imply realtime socket support, global-chat sending, moderation controls, or a fully known event schema.

## Referral

Implemented and observed: read referral code/stats, check code availability, update referral code. CLI writes require `--yes`.

## CLI

Common commands include authentication (`login`, `login-apple`, `logout`, `refresh`), account reads, markets, market detail, activity, charts, prices, transactions, buy/sell, settlement claim, comments, follow/unfollow, referral operations, notification read-all, ad-reward claim, user inspection and raw requests.

CLI implementation footprint: `cli_parser.py` 135 lines + `cli_dispatch.py` 192 + `cli.py` 28 = **355 physical lines**.

State-changing commands require explicit `--yes` where defined.

## Local reliability features

Poyto additionally implements credential-source priority, environment configuration, token-file parsing, configurable hosts/timeouts, reusable device metadata headers, context-manager support, `py.typed`, normalized API exceptions, secret-masked session inspection, network-free MockTransport tests, Ruff, mypy, package build and Python 3.10–3.14 CI.

## Raw HTTP escape hatch

`PoytoClient.request(...)` and CLI `raw` can call an explicit caller-supplied route. That is an escape hatch, **not** evidence that arbitrary endpoints are supported.

## What supported means

“Supported” means Poyto has a maintained surface and suitable tests for the request shape/local behavior. It does not mean POYP guarantees the endpoint or that all responses and server rules are known.

For everything that lacks enough evidence, see [`known-gaps.md`](known-gaps.md). For the route inventory, see [`endpoints.md`](endpoints.md).
