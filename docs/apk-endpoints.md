# POYP Android APK endpoint inventory

POYP Android 1.3.8 の実 APK を 2026-09-10 に再確認し、`assets/index.android.bundle` を取り出して Hermes を再逆コンパイルしたうえで、POYP の request helper 呼び出しまで追跡して復元した API 一覧。合計 **129 method + path pairs**。そのうち **56件**は `docs/endpoints.md` の既存 HAR/runtime 記録と HTTP method + normalized path が完全一致し、**73件**は APK/Hermes 側でのみ確認できた。

## Artifact provenance

- APK: `.analysis/POYP-1.3.8.apk`
- APK SHA-256: `2F3494E9F95B1BB4BEB39C3CED57F9C1926D304BD1EB950F4426538CC70472D4`
- extracted `assets/index.android.bundle` SHA-256: `FF9CE7DEFB6E0F096B41F78032F03EFE571D3D824997A9FE8DD1FFC9E7298348`
- fresh Hermes decompile SHA-256: `6C6FE188DFFFF67C1F1BF4D72093711DD814FA1587E5D1B6DB11663220683A55`
- fresh decompile と従来の `.analysis/decompiled.js` は SHA-256 が一致したため、既存解析結果も同一 bundle 由来であることを確認済み

## Evidence rules

`static-call` は、Hermes 逆コンパイル結果で **関数名 + request helper の実呼び出し + HTTP method + route construction** を復元できたもの。下表の `APK function` と `Decompiled call` がその根拠で、今回の129件はすべて `static-call` まで確認できた。`static-string` は APK/XAPK 内の生文字列しか根拠がない弱い証拠で、この表には採用していない。

`Documented observed = yes` は、`docs/endpoints.md` の観測済みルート一覧に同じ HTTP method + normalized path があることを示す。説明文に出てくる static-only ルートは数えない。`no` の73件は「現行 APK に呼び出し実装がある」ことまでは確認済みだが、現在のサーバーで成功することまでは保証しないため observed へ昇格させていない。

動的パスは Hermes の関数名と route construction から `marketId`、`userId`、`commentId`、`messageId`、`teamId`、`entryId`、`campaignResultId` などへ正規化した。Query/body keys は静的に復元できたものだけを記載するため、`-` は「存在しない」ではなく「静的には確定できなかった」を含む。

### Excluded noise / stale-candidate handling

APK の生文字列走査では POYP API 以外の SDK・telemetry 由来文字列も混ざる。たとえば `/api/broadcast` のような unrelated SDK route や Sentry 系文字列は、`api.poyp.app` の request helper call-site に結び付かないため除外する。関数名に `debug` / `mock` / `dummy` / `legacy` などが付く候補も再確認したが、今回採用した129件にその種の明示的なデバッグ・ダミー・旧API関数は見つからなかった。

なお `_fetchWorldCupFixtures` などの `WorldCup` は文字列検索で `old` を含むように見える false positive になり得るが、legacy 判定には使っていない。今後クライアント実装で static-only route を使う場合も、まず `Documented observed = yes` を優先し、`no` は runtime/HAR で再検証してから通常機能へ昇格する。

| Evidence | Method | Host | Path | Query keys | Body keys | APK function | Decompiled call | Documented observed | Statuses |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| static-call | DELETE | `api.poyp.app` | `/api/comments/{commentId}` | - | - | `_deleteComment` | `decompiled.js:967933` | yes | - |
| static-call | DELETE | `api.poyp.app` | `/api/comments/{commentId}/likes` | - | - | `_unlikeComment` | `decompiled.js:968065` | no | - |
| static-call | DELETE | `api.poyp.app` | `/api/global-chat/messages/{messageId}/likes` | - | - | `_unlikeGlobalChatMessage` | `decompiled.js:968401` | no | - |
| static-call | DELETE | `api.poyp.app` | `/api/me/account` | - | - | `_deleteAccount` | `decompiled.js:978323` | no | - |
| static-call | DELETE | `api.poyp.app` | `/api/me/push-tokens` | - | `token` | `_deletePushToken` | `decompiled.js:975004` | no | - |
| static-call | DELETE | `api.poyp.app` | `/api/teams/{teamId}/follow` | - | - | `_unfollowTeam` | `decompiled.js:977391` | no | - |
| static-call | DELETE | `api.poyp.app` | `/api/users/{userId}/block` | - | - | `_unblockUser` | `decompiled.js:976763` | no | - |
| static-call | DELETE | `api.poyp.app` | `/api/users/{userId}/follow` | - | - | `_unfollowUser` | `decompiled.js:976957` | yes | - |
| static-call | GET | `api.poyp.app` | `/api/campaign-banners` | - | - | `_fetchCampaignBanners` | `decompiled.js:966098` | yes | - |
| static-call | GET | `api.poyp.app` | `/api/check-username/{username}` | - | - | `_checkUsernameAvailability` | `decompiled.js:965494` | no | - |
| static-call | GET | `api.poyp.app` | `/api/comments/moderation-status` | - | - | `_fetchCommentModerationStatus` | `decompiled.js:976849` | yes | - |
| static-call | GET | `api.poyp.app` | `/api/eraberu-pay/rate` | - | - | `_fetchEraberuPayRate` | `decompiled.js:975374` | no | - |
| static-call | GET | `api.poyp.app` | `/api/faqs` | - | - | `_fetchFaqs` | `decompiled.js:981607` | no | - |
| static-call | GET | `api.poyp.app` | `/api/global-chat/mention-suggestions` | `limit`, `q` | - | `_fetchGlobalChatMentionSuggestions` | `decompiled.js:978136` | no | - |
| static-call | GET | `api.poyp.app` | `/api/global-chat/messages` | `cursor`, `limit` | - | `_fetchGlobalChatMessagesPage` | `decompiled.js:968162` | yes | - |
| static-call | GET | `api.poyp.app` | `/api/home-sections` | - | - | `_fetchHomeSections` | `decompiled.js:965964` | yes | - |
| static-call | GET | `api.poyp.app` | `/api/home-tabs` | - | - | `_fetchHomeTabs` | `decompiled.js:965719` | yes | - |
| static-call | GET | `api.poyp.app` | `/api/interests/{category}/subcategories` | - | - | `_fetchSubcategories` | `decompiled.js:965837` | yes | - |
| static-call | GET | `api.poyp.app` | `/api/leaderboard/recent-comments` | `limit`, `offset` | - | `_fetchRecentComments` | `decompiled.js:979246` | yes | - |
| static-call | GET | `api.poyp.app` | `/api/leaderboard/recent-trades` | - | - | `_fetchRecentTrades` | `decompiled.js:979763` | yes | - |
| static-call | GET | `api.poyp.app` | `/api/leaderboard/rising-markets` | `limit`, `offset`, `period` | - | `_fetchRisingMarkets` | `decompiled.js:980409` | yes | - |
| static-call | GET | `api.poyp.app` | `/api/leaderboard/traders` | `limit`, `offset`, `period` | - | `_fetchTopTraders` | `decompiled.js:978987` | yes | - |
| static-call | GET | `api.poyp.app` | `/api/live-moments` | `limit` | - | `_fetchLiveMoments` | `decompiled.js:978877` | no | - |
| static-call | GET | `api.poyp.app` | `/api/live-stats/{id}` | - | - | `_fetchLiveStats` | `decompiled.js:978696` | no | - |
| static-call | GET | `api.poyp.app` | `/api/markets` | `cursor`, `feed`, `interestId`, `limit`, `phase`, `search`, `sort` | - | `_fetchMarkets` | `decompiled.js:965646` | yes | - |
| static-call | GET | `api.poyp.app` | `/api/markets/{marketId}` | - | - | `_fetchMarket` | `decompiled.js:966268` | yes | - |
| static-call | GET | `api.poyp.app` | `/api/markets/{marketId}/activity` | `cursor`, `limit`, `types` | - | `_fetchMarketActivityPage` | `decompiled.js:967499` | yes | - |
| static-call | GET | `api.poyp.app` | `/api/markets/{marketId}/chart` | `tf` | - | `_fetchMarketChart` | `decompiled.js:966457` | no | - |
| static-call | GET | `api.poyp.app` | `/api/markets/{marketId}/comments` | `cursor`, `limit` | - | `_fetchMarketCommentsPage` | `decompiled.js:967244` | no | - |
| static-call | GET | `api.poyp.app` | `/api/markets/{marketId}/mention-suggestions` | `limit`, `q` | - | `_fetchMarketMentionSuggestions` | `decompiled.js:977964` | no | - |
| static-call | GET | `api.poyp.app` | `/api/markets/{marketId}/related` | `limit` | - | `_fetchRelatedMarkets` | `decompiled.js:966352` | yes | - |
| static-call | GET | `api.poyp.app` | `/api/markets/{marketId}/screen-auxiliary` | `tf` | - | `_fetchMarketScreenAuxiliary` | `decompiled.js:966716` | yes | - |
| static-call | GET | `api.poyp.app` | `/api/markets/{marketId}/screen-bundle` | `tf` | - | `_fetchMarketScreenBundle` | `decompiled.js:966554` | no | - |
| static-call | GET | `api.poyp.app` | `/api/markets/{marketId}/trades` | `cursor`, `limit` | - | `_fetchMarketTrades` | `decompiled.js:967093` | no | - |
| static-call | GET | `api.poyp.app` | `/api/markets/{marketId}/voters` | - | - | `_fetchMarketVoters` | `decompiled.js:967599` | no | - |
| static-call | GET | `api.poyp.app` | `/api/me/balance-history` | `tf` | - | `_fetchBalanceHistory` | `decompiled.js:978389` | yes | - |
| static-call | GET | `api.poyp.app` | `/api/me/balances` | - | - | `_fetchMeBalances` | `decompiled.js:966905` | yes | - |
| static-call | GET | `api.poyp.app` | `/api/me/blocked-users` | - | - | `_fetchBlockedUsers` | `decompiled.js:976806` | yes | - |
| static-call | GET | `api.poyp.app` | `/api/me/campaign-results` | - | - | `_fetchCampaignResults` | `decompiled.js:968591` | yes | - |
| static-call | GET | `api.poyp.app` | `/api/me/coin-history` | `cursor`, `limit` | - | `_fetchCoinHistory` | `decompiled.js:975903` | no | - |
| static-call | GET | `api.poyp.app` | `/api/me/eraberu-pay/history` | `cursor`, `limit` | - | `_fetchEraberuPayHistory` | `decompiled.js:975500` | no | - |
| static-call | GET | `api.poyp.app` | `/api/me/login-streak` | - | - | `_getLoginStreak` | `decompiled.js:970021` | yes | - |
| static-call | GET | `api.poyp.app` | `/api/me/loss-gacha/status` | `marketId` | - | `_fetchLossGachaStatus` | `decompiled.js:970629` | yes | - |
| static-call | GET | `api.poyp.app` | `/api/me/markets/{marketId}/positions` | - | - | `_fetchMyMarketPositions` | `decompiled.js:969108` | yes | - |
| static-call | GET | `api.poyp.app` | `/api/me/missions` | - | - | `_fetchMeMissions` | `decompiled.js:969401` | yes | - |
| static-call | GET | `api.poyp.app` | `/api/me/notification-preferences` | - | - | `_fetchNotificationPreferences` | `decompiled.js:975106` | no | - |
| static-call | GET | `api.poyp.app` | `/api/me/notifications` | `cursor`, `limit`, `type` | - | `_fetchMeNotifications` | `decompiled.js:974700` | yes | - |
| static-call | GET | `api.poyp.app` | `/api/me/notifications/unread-count` | - | - | `_fetchMeUnreadCount` | `decompiled.js:974748` | yes | - |
| static-call | GET | `api.poyp.app` | `/api/me/portfolio` | - | - | `_fetchMePortfolio` | `decompiled.js:968523` | yes | - |
| static-call | GET | `api.poyp.app` | `/api/me/portfolio/history` | `cursor`, `limit`, `search`, `sort`, `tab` | - | `_fetchMePortfolioHistory` | `decompiled.js:968892` | yes | - |
| static-call | GET | `api.poyp.app` | `/api/me/profile` | - | - | `_fetchMeProfile` | `decompiled.js:965211` | yes | - |
| static-call | GET | `api.poyp.app` | `/api/me/provider-rewards` | `since`, `source` | - | `_getProviderRewards` | `decompiled.js:978538` | yes | - |
| static-call | GET | `api.poyp.app` | `/api/me/referral-code` | - | - | `_fetchReferralCodeInfo` | `decompiled.js:976250` | yes | - |
| static-call | GET | `api.poyp.app` | `/api/me/referral-code/availability` | `code` | - | `_checkReferralCodeAvailability` | `decompiled.js:976356` | yes | - |
| static-call | GET | `api.poyp.app` | `/api/me/referral-stats` | - | - | `_fetchReferralStats` | `decompiled.js:976049` | yes | - |
| static-call | GET | `api.poyp.app` | `/api/me/trades` | `cursor`, `limit`, `status` | - | `_fetchMeTradeHistory` | `decompiled.js:969353` | no | - |
| static-call | GET | `api.poyp.app` | `/api/me/wc-bracket` | - | - | `_fetchMyWcBracket` | `decompiled.js:980909` | no | - |
| static-call | GET | `api.poyp.app` | `/api/onboarding` | - | - | `_fetchOnboardingQuestionnaire` | `decompiled.js:964950` | yes | - |
| static-call | GET | `api.poyp.app` | `/api/onboarding/validate-referral` | `code` | - | `_validateReferralCode` | `decompiled.js:965113` | no | - |
| static-call | GET | `api.poyp.app` | `/api/prices/{asset}` | - | - | `_fetchAssetCurrentPrice` | `decompiled.js:978755` | yes | - |
| static-call | GET | `api.poyp.app` | `/api/safety` | - | - | `_fetchSafety` | `decompiled.js:981728` | no | - |
| static-call | GET | `api.poyp.app` | `/api/search/sections` | - | - | `_fetchSearchSections` | `decompiled.js:980229` | yes | - |
| static-call | GET | `api.poyp.app` | `/api/teams` | `league` | - | `_fetchTeams` | `decompiled.js:977283` | no | - |
| static-call | GET | `api.poyp.app` | `/api/timeline/followed-trades` | - | - | `_fetchFollowedTimeline` | `decompiled.js:980137` | yes | - |
| static-call | GET | `api.poyp.app` | `/api/users/search` | `limit`, `q` | - | `_fetchUsersSearch` | `decompiled.js:977776` | no | - |
| static-call | GET | `api.poyp.app` | `/api/users/{userId}` | - | - | `_fetchUserProfile` | `decompiled.js:977544` | yes | - |
| static-call | GET | `api.poyp.app` | `/api/users/{userId}/balance-history` | `tf` | - | `_fetchUserBalanceHistory` | `decompiled.js:978470` | yes | - |
| static-call | GET | `api.poyp.app` | `/api/users/{userId}/follow-status` | - | - | `_fetchFollowStatus` | `decompiled.js:977008` | yes | - |
| static-call | GET | `api.poyp.app` | `/api/users/{userId}/followers` | `cursor`, `limit` | - | `_fetchFollowers` | `decompiled.js:977108` | yes | - |
| static-call | GET | `api.poyp.app` | `/api/users/{userId}/following` | `cursor`, `limit` | - | `_fetchFollowing` | `decompiled.js:977210` | yes | - |
| static-call | GET | `api.poyp.app` | `/api/users/{userId}/portfolio` | - | - | `_fetchUserPortfolio` | `decompiled.js:969178` | no | - |
| static-call | GET | `api.poyp.app` | `/api/users/{userId}/portfolio/history` | `cursor`, `limit`, `search`, `sort`, `tab` | - | `_fetchUserPortfolioHistory` | `decompiled.js:969041` | yes | - |
| static-call | GET | `api.poyp.app` | `/api/users/{userId}/team-follows` | - | - | `_fetchUserTeamFollows` | `decompiled.js:977442` | yes | - |
| static-call | GET | `api.poyp.app` | `/api/users/{userId}/wc-bracket` | - | - | `_fetchUserWcBracketRaw` | `decompiled.js:981191` | no | - |
| static-call | GET | `api.poyp.app` | `/api/walking-challenge/history` | - | - | `_fetchWalkingChallengeHistory` | `decompiled.js:982084` | no | - |
| static-call | GET | `api.poyp.app` | `/api/walking-challenge/status` | - | - | `_fetchWalkingChallengeStatus` | `decompiled.js:981812` | yes | - |
| static-call | GET | `api.poyp.app` | `/api/worldcup/bracket` | - | - | `_fetchWorldCupBracket` | `decompiled.js:980826` | no | - |
| static-call | GET | `api.poyp.app` | `/api/worldcup/confirmed-slots` | - | - | `_fetchWcConfirmedSlots` | `decompiled.js:981490` | no | - |
| static-call | GET | `api.poyp.app` | `/api/worldcup/fixtures` | `groupLabel`, `stage` | - | `_fetchWorldCupFixtures` | `decompiled.js:980660` | no | - |
| static-call | GET | `api.poyp.app` | `/api/worldcup/standings` | - | - | `_fetchWorldCupStandings` | `decompiled.js:980743` | no | - |
| static-call | PATCH | `api.poyp.app` | `/api/me/profile` | - | - | `_updateMeProfile` | `decompiled.js:965322` | no | - |
| static-call | PATCH | `api.poyp.app` | `/api/onboarding/questions/selections` | - | `questionIds`, `shownQuestionIds` | `_saveOnboardingQuestionSelections` | `decompiled.js:965060` | no | - |
| static-call | POST | `api.poyp.app` | `/api/adjust-attribution` | - | - | `_upsertAdjustAttribution` | `decompiled.js:965441` | no | - |
| static-call | POST | `api.poyp.app` | `/api/comments/{commentId}/likes` | - | - | `_likeComment` | `decompiled.js:967998` | yes | - |
| static-call | POST | `api.poyp.app` | `/api/comments/{commentId}/report` | - | `description`, `reason` | `_reportComment` | `decompiled.js:976659` | no | - |
| static-call | POST | `api.poyp.app` | `/api/global-chat/messages` | - | - | `_postGlobalChatMessage` | `decompiled.js:968267` | no | - |
| static-call | POST | `api.poyp.app` | `/api/global-chat/messages/{messageId}/likes` | - | - | `_likeGlobalChatMessage` | `decompiled.js:968334` | no | - |
| static-call | POST | `api.poyp.app` | `/api/global-chat/messages/{messageId}/report` | - | `description`, `reason` | `_reportGlobalChatMessage` | `decompiled.js:968477` | no | - |
| static-call | POST | `api.poyp.app` | `/api/markets/{marketId}/comments` | - | - | `_postMarketComment` | `decompiled.js:967781` | yes | - |
| static-call | POST | `api.poyp.app` | `/api/me/ad-rewards/claim` | `source` | - | `_claimAdReward` | `decompiled.js:969843` | yes | - |
| static-call | POST | `api.poyp.app` | `/api/me/campaign-results/{campaignResultId}/claim` | - | - | `_claimCampaignResult` | `decompiled.js:968726` | no | - |
| static-call | POST | `api.poyp.app` | `/api/me/coupons/redeem` | - | `code` | `_redeemCoupon` | `decompiled.js:966961` | no | - |
| static-call | POST | `api.poyp.app` | `/api/me/eraberu-pay/exchange` | - | - | `_executeEraberuPayExchange` | `decompiled.js:975326` | no | - |
| static-call | POST | `api.poyp.app` | `/api/me/eraberu-pay/exchanges/{exchangeId}/resend` | - | `email` | `_resendEraberuPayGift` | `decompiled.js:975564` | no | - |
| static-call | POST | `api.poyp.app` | `/api/me/login-streak/bonus-claim` | - | - | `_claimLoginStreakVideoBonus` | `decompiled.js:970179` | no | - |
| static-call | POST | `api.poyp.app` | `/api/me/login-streak/claim` | - | - | `_claimLoginStreak` | `decompiled.js:970113` | no | - |
| static-call | POST | `api.poyp.app` | `/api/me/loss-gacha/claim` | - | - | `_claimLossGacha` | `decompiled.js:970842` | no | - |
| static-call | POST | `api.poyp.app` | `/api/me/loss-gacha/ticket` | - | `marketId` | `_issueLossGachaAdTicket` | `decompiled.js:970757` | no | - |
| static-call | POST | `api.poyp.app` | `/api/me/missions/{slug}/bonus-claim` | - | - | `_claimMissionBonus` | `decompiled.js:969953` | no | - |
| static-call | POST | `api.poyp.app` | `/api/me/missions/{slug}/claim` | - | - | `_claimMission` | `decompiled.js:969644` | no | - |
| static-call | POST | `api.poyp.app` | `/api/me/missions/{slug}/follow-opened` | - | - | `_notifyMissionFollowOpened` | `decompiled.js:969741` | no | - |
| static-call | POST | `api.poyp.app` | `/api/me/notifications/read` | - | `notificationIds` | `_markNotificationsRead` | `decompiled.js:974809` | no | - |
| static-call | POST | `api.poyp.app` | `/api/me/notifications/read-all` | - | - | `_markAllNotificationsRead` | `decompiled.js:974866` | yes | - |
| static-call | POST | `api.poyp.app` | `/api/me/phone-verification/check` | - | - | `_checkPhoneVerification` | `decompiled.js:976578` | no | - |
| static-call | POST | `api.poyp.app` | `/api/me/phone-verification/send` | - | - | `_sendPhoneVerification` | `decompiled.js:976510` | no | - |
| static-call | POST | `api.poyp.app` | `/api/me/push-tokens` | - | `platform`, `token` | `_registerPushToken` | `decompiled.js:974934` | yes | - |
| static-call | POST | `api.poyp.app` | `/api/me/user-market-proposals` | - | - | `_submitMarketProposal` | `decompiled.js:965265` | no | - |
| static-call | POST | `api.poyp.app` | `/api/me/wc-bracket/entry` | - | - | `_enterMyWcBracket` | `decompiled.js:981085` | no | - |
| static-call | POST | `api.poyp.app` | `/api/onboarding` | - | - | `_submitOnboarding` | `decompiled.js:965165` | no | - |
| static-call | POST | `api.poyp.app` | `/api/onboarding/questions/reached` | - | `shownQuestionIds` | `_reportOnboardingQuestionsReached` | `decompiled.js:965004` | no | - |
| static-call | POST | `api.poyp.app` | `/api/settlements/ad-ticket` | - | - | `_issueSettlementAdTicket` | `decompiled.js:970306` | no | - |
| static-call | POST | `api.poyp.app` | `/api/settlements/claim` | - | - | `_claimSettlement` | `decompiled.js:970375` | no | - |
| static-call | POST | `api.poyp.app` | `/api/settlements/claim-split` | - | - | `_claimSettlementSplit` | `decompiled.js:970941` | no | - |
| static-call | POST | `api.poyp.app` | `/api/settlements/loss-bonus` | - | - | `_claimSettlementLossBonus` | `decompiled.js:970540` | no | - |
| static-call | POST | `api.poyp.app` | `/api/teams/{teamId}/follow` | - | - | `_followTeam` | `decompiled.js:977337` | no | - |
| static-call | POST | `api.poyp.app` | `/api/trades/buy` | - | - | `_submitTradeBuy` | `decompiled.js:969469` | yes | - |
| static-call | POST | `api.poyp.app` | `/api/trades/quote` | - | - | `_fetchTradeQuote` | `decompiled.js:969577` | no | - |
| static-call | POST | `api.poyp.app` | `/api/trades/sell` | - | - | `_submitTradeSell` | `decompiled.js:969523` | yes | - |
| static-call | POST | `api.poyp.app` | `/api/users/{userId}/block` | - | - | `_blockUser` | `decompiled.js:976711` | no | - |
| static-call | POST | `api.poyp.app` | `/api/users/{userId}/follow` | - | - | `_followUser` | `decompiled.js:976903` | yes | - |
| static-call | POST | `api.poyp.app` | `/api/users/{userId}/report` | - | `description`, `reason` | `_reportProfile` | `decompiled.js:978277` | no | - |
| static-call | POST | `api.poyp.app` | `/api/walking-challenge/entries` | - | `platform`, `roundStartsAt`, `stakePoints` | `_enterWalkingChallenge` | `decompiled.js:981871` | no | - |
| static-call | POST | `api.poyp.app` | `/api/walking-challenge/entries/{entryId}/add-stake` | - | `addPoints` | `_addWalkingChallengeStake` | `decompiled.js:982038` | no | - |
| static-call | POST | `api.poyp.app` | `/api/walking-challenge/entries/{entryId}/cancel` | - | - | `_cancelWalkingChallengeEntry` | `decompiled.js:981977` | no | - |
| static-call | PUT | `api.poyp.app` | `/api/comments/{commentId}` | - | - | `_editComment` | `decompiled.js:967867` | yes | - |
| static-call | PUT | `api.poyp.app` | `/api/me/notification-preferences` | - | - | `_updateNotificationPreferences` | `decompiled.js:975160` | no | - |
| static-call | PUT | `api.poyp.app` | `/api/me/referral-code` | - | `code` | `_setReferralCode` | `decompiled.js:976426` | yes | - |
| static-call | PUT | `api.poyp.app` | `/api/me/wc-bracket` | - | - | `_saveMyWcBracket` | `decompiled.js:980996` | no | - |
| static-call | PUT | `api.poyp.app` | `/api/walking-challenge/steps` | - | - | `_syncWalkingChallengeSteps` | `decompiled.js:981923` | no | - |

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
