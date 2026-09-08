# Observed endpoints

This list is based on supplied POYP HAR captures from 2026-09-08. It is an observation log, not an official API specification.

## Authentication

Directly observed:

- `POST /auth/v1/token?grant_type=id_token`
- `POST /auth/v1/logout?scope=global`

The id-token exchange response included an access token and refresh token.

Implemented from standard Supabase/GoTrue behavior, **not directly present in the supplied HARs**:

- `POST /auth/v1/token?grant_type=refresh_token`

See [refresh tokens](refresh-tokens.md) for the distinction.

## Account

- `GET /api/me/profile`
- `GET /api/me/balances`
- `GET /api/me/portfolio`
- `GET /api/me/portfolio/history`
- `GET /api/me/balance-history`
- `GET /api/me/balance-transactions`
- `GET /api/me/expiring-balances`
- `GET /api/me/missions`
- `GET /api/me/login-streak`
- `GET /api/me/campaign-results`
- `GET /api/me/provider-rewards`
- `GET /api/me/loss-gacha/status`
- `GET /api/me/notifications`
- `GET /api/me/notifications/unread-count`
- `POST /api/me/notifications/read-all`
- `POST /api/me/push-tokens`
- `POST /api/me/ad-rewards/claim`
- `GET /api/me/blocked-users`

## Referral

- `GET /api/me/referral-code`
- `PUT /api/me/referral-code`
- `GET /api/me/referral-code/availability`
- `GET /api/me/referral-stats`

## Markets and positions

- `GET /api/markets`
- `GET /api/markets/{marketId}`
- `GET /api/markets/{marketId}/related`
- `GET /api/markets/{marketId}/screen-auxiliary`
- `GET /api/markets/{marketId}/activity`
- `GET /api/markets/charts`
- `GET /api/me/markets/{marketId}/positions`
- `GET /api/prices/{asset}`

## Trading

- `POST /api/trades/buy`
- `POST /api/trades/sell`

Observed buy fields: `marketId`, `positionIndex`, `pointAmount`, `orderSurface`, `requestId`, `displayPreset`, `entryPoint`, `sessionId`, `deviceId`.

Observed sell fields: `marketId`, `positionIndex`, `shares`, `orderSurface`, `entryPoint`, `sessionId`, `deviceId`.

## Comments

- `GET /api/comments/moderation-status`
- `POST /api/markets/{marketId}/comments`
- `PUT /api/comments/{commentId}`
- `DELETE /api/comments/{commentId}`
- `POST /api/comments/{commentId}/likes`

No unlike request was present in the supplied captures.

## Discovery

- `GET /api/home-sections`
- `GET /api/home-tabs`
- `GET /api/search/sections`
- `GET /api/interests/{category}/subcategories`
- `GET /api/campaign-banners`
- `GET /api/onboarding`

## Social and rankings

- `GET /api/global-chat/messages`
- `GET /api/leaderboard/traders`
- `GET /api/leaderboard/recent-trades`
- `GET /api/leaderboard/recent-comments`
- `GET /api/leaderboard/rising-markets`
- `GET /api/timeline/followed-trades`
- `GET /api/users/{userId}`
- `GET /api/users/{userId}/follow-status`
- `GET /api/users/{userId}/team-follows`
- `GET /api/users/{userId}/followers`
- `GET /api/users/{userId}/following`
- `GET /api/users/{userId}/balance-history`
- `GET /api/users/{userId}/portfolio/history`
- `POST /api/users/{userId}/follow`
- `DELETE /api/users/{userId}/follow`

## Misc

- `GET /api/walking-challenge/status`
- `POST /api/events`

Anything not listed as observed here should be treated as unknown until captured or otherwise independently documented.
