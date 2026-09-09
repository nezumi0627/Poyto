# POYP Android APK endpoint inventory

POYP Android 1.3.8 の Hermes bundle を静的解析し、POYP の request helper 呼び出しまで追跡して復元できた API を全件列挙する。合計 **129 method + path pairs**。うち **56件**は `docs/endpoints.md` の既存観測記録と HTTP method + path が完全一致し、**73件**は今回の APK/Hermes 静的解析でのみ確認できた。

`static` は APK 内の実装・呼び出し形が確認できたことを示す。`Documented observed = yes` は、同じ HTTP method + path が既存の HAR/runtime 記録にもあることを示す。今回の作業環境には有効なローカルセッションがなかったため、static-only の73件は call-site、HTTP method、query/body の組み立てを可能な範囲で確認したが、サーバー到達性を示す `observed` へは昇格していない。

動的パスは Hermes の関数名と周辺の route construction から、`marketId`、`userId`、`commentId`、`messageId`、`teamId`、`entryId`、`campaignResultId` などへ正規化している。Query/body keys は bundle から静的に回収できたものだけを記載するため、`-` は「存在しない」とは限らず「静的に確定できなかった」を含む。

| Evidence | Method | Host | Path | Query keys | Body keys | Documented observed | Statuses |
| --- | --- | --- | --- | --- | --- | --- | --- |
| static | DELETE | `api.poyp.app` | `/api/comments/{commentId}` | - | - | yes | - |
| static | DELETE | `api.poyp.app` | `/api/comments/{commentId}/likes` | - | - | no | - |
| static | DELETE | `api.poyp.app` | `/api/global-chat/messages/{messageId}/likes` | - | - | no | - |
| static | DELETE | `api.poyp.app` | `/api/me/account` | - | - | no | - |
| static | DELETE | `api.poyp.app` | `/api/me/push-tokens` | - | `token` | no | - |
| static | DELETE | `api.poyp.app` | `/api/teams/{teamId}/follow` | - | - | no | - |
| static | DELETE | `api.poyp.app` | `/api/users/{userId}/block` | - | - | no | - |
| static | DELETE | `api.poyp.app` | `/api/users/{userId}/follow` | - | - | yes | - |
| static | GET | `api.poyp.app` | `/api/campaign-banners` | - | - | yes | - |
| static | GET | `api.poyp.app` | `/api/check-username/{username}` | - | - | no | - |
| static | GET | `api.poyp.app` | `/api/comments/moderation-status` | - | - | yes | - |
| static | GET | `api.poyp.app` | `/api/eraberu-pay/rate` | - | - | no | - |
| static | GET | `api.poyp.app` | `/api/faqs` | - | - | no | - |
| static | GET | `api.poyp.app` | `/api/global-chat/mention-suggestions` | `limit`, `q` | - | no | - |
| static | GET | `api.poyp.app` | `/api/global-chat/messages` | `cursor`, `limit` | - | yes | - |
| static | GET | `api.poyp.app` | `/api/home-sections` | - | - | yes | - |
| static | GET | `api.poyp.app` | `/api/home-tabs` | - | - | yes | - |
| static | GET | `api.poyp.app` | `/api/interests/{category}/subcategories` | - | - | yes | - |
| static | GET | `api.poyp.app` | `/api/leaderboard/recent-comments` | `limit`, `offset` | - | yes | - |
| static | GET | `api.poyp.app` | `/api/leaderboard/recent-trades` | - | - | yes | - |
| static | GET | `api.poyp.app` | `/api/leaderboard/rising-markets` | `limit`, `offset`, `period` | - | yes | - |
| static | GET | `api.poyp.app` | `/api/leaderboard/traders` | `limit`, `offset`, `period` | - | yes | - |
| static | GET | `api.poyp.app` | `/api/live-moments` | `limit` | - | no | - |
| static | GET | `api.poyp.app` | `/api/live-stats/{id}` | - | - | no | - |
| static | GET | `api.poyp.app` | `/api/markets` | `cursor`, `feed`, `interestId`, `limit`, `phase`, `search`, `sort` | - | yes | - |
| static | GET | `api.poyp.app` | `/api/markets/{marketId}` | - | - | yes | - |
| static | GET | `api.poyp.app` | `/api/markets/{marketId}/activity` | `cursor`, `limit`, `types` | - | yes | - |
| static | GET | `api.poyp.app` | `/api/markets/{marketId}/chart` | `tf` | - | no | - |
| static | GET | `api.poyp.app` | `/api/markets/{marketId}/comments` | `cursor`, `limit` | - | no | - |
| static | GET | `api.poyp.app` | `/api/markets/{marketId}/mention-suggestions` | `limit`, `q` | - | no | - |
| static | GET | `api.poyp.app` | `/api/markets/{marketId}/related` | `limit` | - | yes | - |
| static | GET | `api.poyp.app` | `/api/markets/{marketId}/screen-auxiliary` | `tf` | - | yes | - |
| static | GET | `api.poyp.app` | `/api/markets/{marketId}/screen-bundle` | `tf` | - | no | - |
| static | GET | `api.poyp.app` | `/api/markets/{marketId}/trades` | `cursor`, `limit` | - | no | - |
| static | GET | `api.poyp.app` | `/api/markets/{marketId}/voters` | - | - | no | - |
| static | GET | `api.poyp.app` | `/api/me/balance-history` | `tf` | - | yes | - |
| static | GET | `api.poyp.app` | `/api/me/balances` | - | - | yes | - |
| static | GET | `api.poyp.app` | `/api/me/blocked-users` | - | - | yes | - |
| static | GET | `api.poyp.app` | `/api/me/campaign-results` | - | - | yes | - |
| static | GET | `api.poyp.app` | `/api/me/coin-history` | `cursor`, `limit` | - | no | - |
| static | GET | `api.poyp.app` | `/api/me/eraberu-pay/history` | `cursor`, `limit` | - | no | - |
| static | GET | `api.poyp.app` | `/api/me/login-streak` | - | - | yes | - |
| static | GET | `api.poyp.app` | `/api/me/loss-gacha/status` | `marketId` | - | yes | - |
| static | GET | `api.poyp.app` | `/api/me/markets/{marketId}/positions` | - | - | yes | - |
| static | GET | `api.poyp.app` | `/api/me/missions` | - | - | yes | - |
| static | GET | `api.poyp.app` | `/api/me/notification-preferences` | - | - | no | - |
| static | GET | `api.poyp.app` | `/api/me/notifications` | `cursor`, `limit`, `type` | - | yes | - |
| static | GET | `api.poyp.app` | `/api/me/notifications/unread-count` | - | - | yes | - |
| static | GET | `api.poyp.app` | `/api/me/portfolio` | - | - | yes | - |
| static | GET | `api.poyp.app` | `/api/me/portfolio/history` | `cursor`, `limit`, `search`, `sort`, `tab` | - | yes | - |
| static | GET | `api.poyp.app` | `/api/me/profile` | - | - | yes | - |
| static | GET | `api.poyp.app` | `/api/me/provider-rewards` | `since`, `source` | - | yes | - |
| static | GET | `api.poyp.app` | `/api/me/referral-code` | - | - | yes | - |
| static | GET | `api.poyp.app` | `/api/me/referral-code/availability` | `code` | - | yes | - |
| static | GET | `api.poyp.app` | `/api/me/referral-stats` | - | - | yes | - |
| static | GET | `api.poyp.app` | `/api/me/trades` | `cursor`, `limit`, `status` | - | no | - |
| static | GET | `api.poyp.app` | `/api/me/wc-bracket` | - | - | no | - |
| static | GET | `api.poyp.app` | `/api/onboarding` | - | - | yes | - |
| static | GET | `api.poyp.app` | `/api/onboarding/validate-referral` | `code` | - | no | - |
| static | GET | `api.poyp.app` | `/api/prices/{asset}` | - | - | yes | - |
| static | GET | `api.poyp.app` | `/api/safety` | - | - | no | - |
| static | GET | `api.poyp.app` | `/api/search/sections` | - | - | yes | - |
| static | GET | `api.poyp.app` | `/api/teams` | `league` | - | no | - |
| static | GET | `api.poyp.app` | `/api/timeline/followed-trades` | - | - | yes | - |
| static | GET | `api.poyp.app` | `/api/users/search` | `limit`, `q` | - | no | - |
| static | GET | `api.poyp.app` | `/api/users/{userId}` | - | - | yes | - |
| static | GET | `api.poyp.app` | `/api/users/{userId}/balance-history` | `tf` | - | yes | - |
| static | GET | `api.poyp.app` | `/api/users/{userId}/follow-status` | - | - | yes | - |
| static | GET | `api.poyp.app` | `/api/users/{userId}/followers` | `cursor`, `limit` | - | yes | - |
| static | GET | `api.poyp.app` | `/api/users/{userId}/following` | `cursor`, `limit` | - | yes | - |
| static | GET | `api.poyp.app` | `/api/users/{userId}/portfolio` | - | - | no | - |
| static | GET | `api.poyp.app` | `/api/users/{userId}/portfolio/history` | `cursor`, `limit`, `search`, `sort`, `tab` | - | yes | - |
| static | GET | `api.poyp.app` | `/api/users/{userId}/team-follows` | - | - | yes | - |
| static | GET | `api.poyp.app` | `/api/users/{userId}/wc-bracket` | - | - | no | - |
| static | GET | `api.poyp.app` | `/api/walking-challenge/history` | - | - | no | - |
| static | GET | `api.poyp.app` | `/api/walking-challenge/status` | - | - | yes | - |
| static | GET | `api.poyp.app` | `/api/worldcup/bracket` | - | - | no | - |
| static | GET | `api.poyp.app` | `/api/worldcup/confirmed-slots` | - | - | no | - |
| static | GET | `api.poyp.app` | `/api/worldcup/fixtures` | `groupLabel`, `stage` | - | no | - |
| static | GET | `api.poyp.app` | `/api/worldcup/standings` | - | - | no | - |
| static | PATCH | `api.poyp.app` | `/api/me/profile` | - | - | no | - |
| static | PATCH | `api.poyp.app` | `/api/onboarding/questions/selections` | - | `questionIds`, `shownQuestionIds` | no | - |
| static | POST | `api.poyp.app` | `/api/adjust-attribution` | - | - | no | - |
| static | POST | `api.poyp.app` | `/api/comments/{commentId}/likes` | - | - | yes | - |
| static | POST | `api.poyp.app` | `/api/comments/{commentId}/report` | - | `description`, `reason` | no | - |
| static | POST | `api.poyp.app` | `/api/global-chat/messages` | - | - | no | - |
| static | POST | `api.poyp.app` | `/api/global-chat/messages/{messageId}/likes` | - | - | no | - |
| static | POST | `api.poyp.app` | `/api/global-chat/messages/{messageId}/report` | - | `description`, `reason` | no | - |
| static | POST | `api.poyp.app` | `/api/markets/{marketId}/comments` | - | - | yes | - |
| static | POST | `api.poyp.app` | `/api/me/ad-rewards/claim` | `source` | - | yes | - |
| static | POST | `api.poyp.app` | `/api/me/campaign-results/{campaignResultId}/claim` | - | - | no | - |
| static | POST | `api.poyp.app` | `/api/me/coupons/redeem` | - | `code` | no | - |
| static | POST | `api.poyp.app` | `/api/me/eraberu-pay/exchange` | - | - | no | - |
| static | POST | `api.poyp.app` | `/api/me/eraberu-pay/exchanges/{exchangeId}/resend` | - | `email` | no | - |
| static | POST | `api.poyp.app` | `/api/me/login-streak/bonus-claim` | - | - | no | - |
| static | POST | `api.poyp.app` | `/api/me/login-streak/claim` | - | - | no | - |
| static | POST | `api.poyp.app` | `/api/me/loss-gacha/claim` | - | - | no | - |
| static | POST | `api.poyp.app` | `/api/me/loss-gacha/ticket` | - | `marketId` | no | - |
| static | POST | `api.poyp.app` | `/api/me/missions/{slug}/bonus-claim` | - | - | no | - |
| static | POST | `api.poyp.app` | `/api/me/missions/{slug}/claim` | - | - | no | - |
| static | POST | `api.poyp.app` | `/api/me/missions/{slug}/follow-opened` | - | - | no | - |
| static | POST | `api.poyp.app` | `/api/me/notifications/read` | - | `notificationIds` | no | - |
| static | POST | `api.poyp.app` | `/api/me/notifications/read-all` | - | - | yes | - |
| static | POST | `api.poyp.app` | `/api/me/phone-verification/check` | - | - | no | - |
| static | POST | `api.poyp.app` | `/api/me/phone-verification/send` | - | - | no | - |
| static | POST | `api.poyp.app` | `/api/me/push-tokens` | - | `platform`, `token` | yes | - |
| static | POST | `api.poyp.app` | `/api/me/user-market-proposals` | - | - | no | - |
| static | POST | `api.poyp.app` | `/api/me/wc-bracket/entry` | - | - | no | - |
| static | POST | `api.poyp.app` | `/api/onboarding` | - | - | no | - |
| static | POST | `api.poyp.app` | `/api/onboarding/questions/reached` | - | `shownQuestionIds` | no | - |
| static | POST | `api.poyp.app` | `/api/settlements/ad-ticket` | - | - | no | - |
| static | POST | `api.poyp.app` | `/api/settlements/claim` | - | - | no | - |
| static | POST | `api.poyp.app` | `/api/settlements/claim-split` | - | - | no | - |
| static | POST | `api.poyp.app` | `/api/settlements/loss-bonus` | - | - | no | - |
| static | POST | `api.poyp.app` | `/api/teams/{teamId}/follow` | - | - | no | - |
| static | POST | `api.poyp.app` | `/api/trades/buy` | - | - | yes | - |
| static | POST | `api.poyp.app` | `/api/trades/quote` | - | - | no | - |
| static | POST | `api.poyp.app` | `/api/trades/sell` | - | - | yes | - |
| static | POST | `api.poyp.app` | `/api/users/{userId}/block` | - | - | no | - |
| static | POST | `api.poyp.app` | `/api/users/{userId}/follow` | - | - | yes | - |
| static | POST | `api.poyp.app` | `/api/users/{userId}/report` | - | `description`, `reason` | no | - |
| static | POST | `api.poyp.app` | `/api/walking-challenge/entries` | - | `platform`, `roundStartsAt`, `stakePoints` | no | - |
| static | POST | `api.poyp.app` | `/api/walking-challenge/entries/{entryId}/add-stake` | - | `addPoints` | no | - |
| static | POST | `api.poyp.app` | `/api/walking-challenge/entries/{entryId}/cancel` | - | - | no | - |
| static | PUT | `api.poyp.app` | `/api/comments/{commentId}` | - | - | yes | - |
| static | PUT | `api.poyp.app` | `/api/me/notification-preferences` | - | - | no | - |
| static | PUT | `api.poyp.app` | `/api/me/referral-code` | - | `code` | yes | - |
| static | PUT | `api.poyp.app` | `/api/me/wc-bracket` | - | - | no | - |
| static | PUT | `api.poyp.app` | `/api/walking-challenge/steps` | - | - | no | - |

## Static-only paths vs documented observed routes

- `DELETE /api/comments/{commentId}/likes`
- `DELETE /api/global-chat/messages/{messageId}/likes`
- `DELETE /api/me/account`
- `DELETE /api/me/push-tokens`
- `DELETE /api/teams/{teamId}/follow`
- `DELETE /api/users/{userId}/block`
- `GET /api/check-username/{username}`
- `GET /api/eraberu-pay/rate`
- `GET /api/faqs`
- `GET /api/global-chat/mention-suggestions`
- `GET /api/live-moments`
- `GET /api/live-stats/{id}`
- `GET /api/markets/{marketId}/chart`
- `GET /api/markets/{marketId}/comments`
- `GET /api/markets/{marketId}/mention-suggestions`
- `GET /api/markets/{marketId}/screen-bundle`
- `GET /api/markets/{marketId}/trades`
- `GET /api/markets/{marketId}/voters`
- `GET /api/me/coin-history`
- `GET /api/me/eraberu-pay/history`
- `GET /api/me/notification-preferences`
- `GET /api/me/trades`
- `GET /api/me/wc-bracket`
- `GET /api/onboarding/validate-referral`
- `GET /api/safety`
- `GET /api/teams`
- `GET /api/users/search`
- `GET /api/users/{userId}/portfolio`
- `GET /api/users/{userId}/wc-bracket`
- `GET /api/walking-challenge/history`
- `GET /api/worldcup/bracket`
- `GET /api/worldcup/confirmed-slots`
- `GET /api/worldcup/fixtures`
- `GET /api/worldcup/standings`
- `PATCH /api/me/profile`
- `PATCH /api/onboarding/questions/selections`
- `POST /api/adjust-attribution`
- `POST /api/comments/{commentId}/report`
- `POST /api/global-chat/messages`
- `POST /api/global-chat/messages/{messageId}/likes`
- `POST /api/global-chat/messages/{messageId}/report`
- `POST /api/me/campaign-results/{campaignResultId}/claim`
- `POST /api/me/coupons/redeem`
- `POST /api/me/eraberu-pay/exchange`
- `POST /api/me/eraberu-pay/exchanges/{exchangeId}/resend`
- `POST /api/me/login-streak/bonus-claim`
- `POST /api/me/login-streak/claim`
- `POST /api/me/loss-gacha/claim`
- `POST /api/me/loss-gacha/ticket`
- `POST /api/me/missions/{slug}/bonus-claim`
- `POST /api/me/missions/{slug}/claim`
- `POST /api/me/missions/{slug}/follow-opened`
- `POST /api/me/notifications/read`
- `POST /api/me/phone-verification/check`
- `POST /api/me/phone-verification/send`
- `POST /api/me/user-market-proposals`
- `POST /api/me/wc-bracket/entry`
- `POST /api/onboarding`
- `POST /api/onboarding/questions/reached`
- `POST /api/settlements/ad-ticket`
- `POST /api/settlements/claim`
- `POST /api/settlements/claim-split`
- `POST /api/settlements/loss-bonus`
- `POST /api/teams/{teamId}/follow`
- `POST /api/trades/quote`
- `POST /api/users/{userId}/block`
- `POST /api/users/{userId}/report`
- `POST /api/walking-challenge/entries`
- `POST /api/walking-challenge/entries/{entryId}/add-stake`
- `POST /api/walking-challenge/entries/{entryId}/cancel`
- `PUT /api/me/notification-preferences`
- `PUT /api/me/wc-bracket`
- `PUT /api/walking-challenge/steps`
