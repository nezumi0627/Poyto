# Python API

## Client

```python
from poyto import PoytoClient

client = PoytoClient(access_token="...")
```

Or load `POYP_*` environment variables:

```python
client = PoytoClient.from_env()
```

Use it as a context manager so the underlying `httpx.Client` is closed automatically.

## Authentication

- `login_with_apple(...)`
- `refresh(...)`
- `set_access_token(...)`
- `logout(...)`

## Account

- `profile()`
- `balances()`
- `portfolio()` / `portfolio_history()`
- `balance_history()` / `balance_transactions()`
- `missions()` / `login_streak()`
- `notifications()` / `unread_notification_count()`
- `mark_all_notifications_read()`
- `provider_rewards()` / `claim_ad_reward()`
- `blocked_users()` / `walking_challenge_status()`

## Markets and trading

- `markets()` / `iter_markets()`
- `market()` / `related_markets()`
- `market_screen_auxiliary()` / `market_activity()` / `market_charts()`
- `my_market_positions()`
- `asset_price()`
- `buy(...)`
- `sell(...)`

Example:

```python
with PoytoClient.from_env() as client:
    market = client.market("MARKET_ID")
    positions = client.my_market_positions("MARKET_ID")
```

## Comments and social

- `post_comment()` / `edit_comment()` / `delete_comment()` / `like_comment()`
- `user_profile()`
- `user_follow_status()`
- `user_followers()` / `user_following()`
- `follow_user()` / `unfollow_user()`
- `user_balance_history()` / `user_portfolio_history()`

## Generic requests

```python
client.request("GET", "/api/path")
client.get("/api/path")
client.post("/api/path", json={"key": "value"})
client.put(...)
client.patch(...)
client.delete(...)
```

These helpers use the same POYP headers and error handling as the dedicated methods.

## Exceptions

- `PoytoError` — base exception
- `AuthenticationError` — credentials/session missing
- `APIError` — non-success API response; exposes `status_code`, `method`, `url`, and `response_body`

## Models

`AuthSession` holds Supabase session fields. `DeviceInfo` controls the observed `x-poyp-*` headers and can be populated from environment variables.
