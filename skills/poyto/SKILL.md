# Poyto Skill

Use Poyto when the user wants to inspect or operate POYP from an AI conversation.

## Preferred interface

Prefer the Poyto MCP tools when they are connected. They expose read-only account/market tools plus guarded buy/sell tools.

Authentication must come from Poyto's local persisted session or environment configuration. Never ask the user to paste an access token, refresh token, Apple identity token, cookie, or stable device identifier into a chat.

## Read operations

Use these freely when needed to answer the user's request:

- `health` — service reachability
- `profile` — account profile
- `balances` — points/balances
- `portfolio` — current positions
- `markets` — market discovery/listing
- `market` — one market by ID
- `market_activity` — activity for one market
- `asset_price` — observed asset-price endpoint
- `transactions` — account point/balance transactions

When comparing markets, fetch the specific market details before giving a confident recommendation. Treat server values as current facts and avoid inventing settlement rules, fees, slippage, limits, or formulas that Poyto has not verified.

## Mutating operations

`buy` and `sell` change account state and require `confirm=true`.

Before calling either tool, make sure the user has explicitly confirmed all of the following in the current request or immediately preceding context:

- exact market
- exact position/side
- exact amount (points or shares)

Do not convert a vague statement such as "bet on the best one" into a trade. First inspect the market, explain what will happen, and obtain explicit confirmation of the concrete operation.

For scheduled or recurring operations, default to read-only monitoring. Do not schedule recurring buys/sells unless the user explicitly asks for the exact recurring transaction and understands that it will execute repeatedly.

## Scheduling

Poyto itself does not need to own the scheduler. Use the host agent's scheduler/automation system and have each scheduled run call the Poyto MCP tools.

Good scheduled tasks include:

- every morning: summarize balances, portfolio, and notable open markets
- every hour: check a specific market and notify only when a threshold/condition is met
- daily: summarize transaction changes
- before a known market deadline: re-check market details and notify the user

When a task is condition-based, only notify when the condition becomes true. Do not spam unchanged results.

## CLI fallback

If MCP is not available but shell execution is available, use the Poyto CLI. Read examples:

```bash
poyto profile
poyto balances
poyto portfolio
poyto markets --limit 20
poyto market MARKET_ID
```

State-changing CLI commands require `--yes` and should follow the same confirmation rules:

```bash
poyto buy MARKET_ID POSITION_INDEX POINTS --yes
poyto sell MARKET_ID POSITION_INDEX SHARES --yes
```

## Setup

Install agent support:

```bash
pip install -e '.[agent]'
```

Run as a local stdio MCP server:

```bash
poyto-mcp
```

Run as an HTTP MCP server for a compatible remote/chat connector:

```bash
poyto-mcp --transport streamable-http --host 127.0.0.1 --port 8765
```

If the chat service cannot reach localhost, expose it through an authenticated tunnel rather than binding Poyto directly to the public internet.
