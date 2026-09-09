# MCP tool groups

## Read

- `health`
- `profile`
- `balances`
- `portfolio`
- `markets`
- `market`
- `market_activity`
- `asset_price`
- `transactions`
- `login_bonus`
- `unread_notification_count`
- `loss_gacha_status`

## Mutations

The following tools are omitted in read-only mode and require `confirm=true` when enabled:

- `buy`
- `sell`
- `loss_gacha_ticket`
- `loss_gacha_claim`

The exact POYP support boundary remains defined by the client/resource modules and capability documentation.
