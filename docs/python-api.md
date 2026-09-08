# Python API

## Client

Recommended usage:

```python
from poyto import PoytoClient

with PoytoClient() as client:
    print(client.profile())
```

Credential sources are resolved automatically. You may also be explicit:

```python
PoytoClient(token="...")
PoytoClient(token_file="token.env")
PoytoClient(access_token="...", refresh_token="...")
```

`PoytoClient.from_env()` is retained for readability and behaves the same as `PoytoClient()` because environment resolution is built into the client.

## Authentication and credentials

- `login(token, refresh_token=None, persist=True)`
- `login_file(path, persist=True)`
- `login_with_apple(...)`
- `refresh(...)`
- `set_access_token(...)`
- `logout(scope="global", local_only=False)`

Token files may be plaintext, JSON, or dotenv-style. See [configuration](configuration.md) and [authentication](authentication.md).

## Account

- `health()`
- `profile()`
- `balances()`
- `portfolio()` / `portfolio_history()`
- `balance_history()` / `balance_transactions()`
- `expiring_balances()`
- `missions()` / `login_streak()`
- `campaign_results()`
- `provider_rewards()` / `loss_gacha_status()`
- `notifications()` / `unread_notification_count()`
- `mark_all_notifications_read()` / `register_push_token()`
- `claim_ad_reward()`
- `blocked_users()` / `walking_challenge_status()`
- `referral_code()` / `referral_stats()` / `referral_code_available()` / `set_referral_code()`

## Markets

- `markets()` / `iter_markets()`
- `market()` / `related_markets()`
- `market_screen_auxiliary()`
- `my_market_positions()`
- `market_activity()` / `market_charts()`
- `asset_price()`
- `comment_moderation_status()`

`asset_price("BTC")` uses the observed `/api/prices/BTC` route.

## Trades

- `buy(...)`
- `sell(...)`

These request shapes are based on supplied HAR captures. They can affect account points/positions.

## Comments and social

- `post_comment()` / `edit_comment()` / `delete_comment()` / `like_comment()`
- `global_chat()`
- `leaderboard_traders()` / `recent_trades()` / `recent_comments()` / `rising_markets()`
- `followed_trades()`
- `user_profile()` / `user_follow_status()` / `user_team_follows()`
- `user_followers()` / `user_following()`
- `user_balance_history()` / `user_portfolio_history()`
- `follow_user()` / `unfollow_user()`

## Discovery

- `home_sections()` / `home_tabs()`
- `search_sections()`
- `interest_subcategories()`
- `campaign_banners()`
- `onboarding()`

## Events

- `make_event(...)`
- `send_events(...)`

## Generic requests

```python
client.request("GET", "/api/path")
client.get("/api/path")
client.post("/api/path", json={"key": "value"})
client.put(...)
client.patch(...)
client.delete(...)
```

These use the same headers and error handling as dedicated resource methods.

## Exceptions

- `PoytoError` — base exception
- `CredentialError` — invalid/missing token file content
- `AuthenticationError` — credentials/session missing
- `APIError` — non-success API response; exposes `status_code`, `method`, `url`, and `response_body`

## Models and configuration

- `AuthSession` — access/refresh token and expiry metadata
- `DeviceInfo` — observed `x-poyp-*` device headers
- `Settings` — normalized environment-backed configuration
- `SessionStore` — persistent local session storage

See [architecture](architecture.md) for module responsibilities.
