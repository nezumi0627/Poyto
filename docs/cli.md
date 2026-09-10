# CLI reference

The package installs the `poyto` command.

## Global credential options

```text
poyto [--token TOKEN_OR_SOURCE] [--refresh-token TOKEN] [--token-file PATH] COMMAND ...
```

If omitted, the same environment/session resolver used by `PoytoClient()` is used automatically.

## Authentication

```text
poyto login [TOKEN_OR_SOURCE] [--refresh-token TOKEN]
poyto login-apple [--id-token TOKEN] [--apple-access-token TOKEN] [--nonce VALUE]
poyto refresh
poyto logout [--local-only]
```

`poyto login` prompts without terminal echo when its token argument is omitted. `login-apple` also reads `POYTO_APPLE_ID_TOKEN`, `POYTO_APPLE_ACCESS_TOKEN`, and `POYTO_APPLE_NONCE` (plus legacy `POYP_*` aliases).

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
poyto settlement-claim MARKET_ID POSITION_INDEX --yes
poyto settlement-claim MARKET_ID --coin-ratio 60 --yes
poyto settlement-claim MARKET_ID --coin-ratio 60 --ticket-id TICKET_ID --yes
```

Without `--coin-ratio`, `settlement-claim` uses the existing implemented/inferred settlement
request shape and requires `POSITION_INDEX`. With `--coin-ratio`, it uses the
APK-static-established split request and does not require `POSITION_INDEX`. Ratios are selected in
10% steps from `0` (all points) through `100` (all coins). `--ticket-id` is optional and is accepted
only together with `--coin-ratio`. Independent live-success evidence is still missing.

## Raw request escape hatch

```text
poyto raw GET /api/some/new-endpoint
poyto raw POST /api/some/new-endpoint --json '{"key":"value"}'
```

Use `raw` only for endpoints you have independently observed or documented. Poyto intentionally does not invent request shapes for unseen APIs.

See [configuration](configuration.md) for the full environment-variable matrix.
