# CLI reference

The package installs the `poyto` command.

## Read-only commands

```text
poyto health
poyto profile
poyto balances
poyto portfolio
poyto missions
poyto streak
poyto referral
poyto notifications
poyto home
poyto walking
poyto markets [--limit N] [--phase open] [--feed home] [--sort recommended]
poyto market MARKET_ID
poyto activity MARKET_ID [--limit N] [--types all|comment|...]
poyto charts MARKET_ID [MARKET_ID ...] [--tf max]
poyto price [BTC]
poyto transactions [--currency point] [--limit N] [--cursor CURSOR]
poyto user USER_ID [--tab active] [--sort newest]
poyto referral-available CODE
```

## Authentication

```text
poyto login-apple
poyto refresh
```

Credentials can be supplied through `POYP_ACCESS_TOKEN`, `POYP_REFRESH_TOKEN`, `POYP_APPLE_ID_TOKEN`, `POYP_APPLE_ACCESS_TOKEN`, and `POYP_APPLE_NONCE`.

## State-changing commands

These require `--yes`:

```text
poyto buy MARKET_ID POSITION_INDEX POINT_AMOUNT --yes
poyto sell MARKET_ID POSITION_INDEX SHARES --yes
poyto comment MARKET_ID BODY --yes
poyto edit-comment COMMENT_ID BODY --yes
poyto delete-comment COMMENT_ID --yes
poyto like-comment COMMENT_ID --yes
poyto follow USER_ID --yes
poyto unfollow USER_ID --yes
poyto set-referral CODE --yes
poyto claim-ad-reward --yes
```

## Raw request escape hatch

```text
poyto raw GET /api/some/new-endpoint
poyto raw POST /api/some/new-endpoint --json '{"key":"value"}'
```

Use `raw` only for endpoints you have independently observed or documented. Poyto intentionally does not invent request shapes for unseen APIs.
