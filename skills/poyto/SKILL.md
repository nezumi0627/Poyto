# Poyto Skill

Use Poyto when the user wants to inspect or operate POYP from an AI conversation. The user should be able to give a normal one-sentence instruction; do not require CLI syntax or tool names when intent can be safely understood from context.

## Conversation behavior

Reply in the language the user normally uses in the current conversation. If the user explicitly requests another language, use that language. Keep exact market IDs, tool names, amounts, and numeric values unchanged. Prefer short, practical responses unless the user asks for detail.

When the user refers to "this market", "this position", or similar context, resolve it from the current conversation or fresh Poyto data when possible rather than making them repeat IDs. Ask only when the reference cannot be resolved safely.

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

For recurring buys/sells, require an explicit exact repeated transaction: market, side/position, amount, and recurrence. For conditional recurring mutations, also require an explicit testable condition. Never invent the condition or amount.

## Scheduling

Poyto itself does not need to own the scheduler. Use the host agent's scheduler/automation system and have each scheduled run call the Poyto MCP tools with fresh server state.

For one-market or one-position monitoring, prefer adaptive scheduling over a fixed loop. Derive the next interval from remaining time, observed activity, requested urgency, and the scheduler's minimum supported frequency. A reasonable default cadence is:

- more than 7 days remaining: every 12–24 hours
- 2–7 days: every 6 hours
- 12–48 hours: every 2 hours
- 3–12 hours: every 30–60 minutes
- 30 minutes–3 hours: every 15 minutes
- under 30 minutes: every 5 minutes, subject to host limits

Lengthen intervals for inactive markets and shorten them for meaningful changes or an imminent deadline. Stop automatically when the market closes/resolves or the tracked position no longer exists. If the host cannot dynamically reschedule one task, use the nearest safe fixed interval or staged schedules.

When a task is condition-based, notify only when the condition becomes true or a meaningful change occurs. Do not spam unchanged results.

## One-sentence examples

The following should be understandable as-is from a chat:

- `この市場を終了まで追って、残り時間に合わせて確認間隔を自動で変えて、重要な変化だけ日本語で教えて。`
- `このポジションを終わるまで追って、残り時間と値動きから確認間隔を自動調整して、売る判断が必要になった時だけ教えて。`
- `毎日1回、注目市場と自分のポートフォリオを確認して、取引した方がよさそうなものがあれば日本語で短く教えて。`
- `毎日9時にこの市場のYESへ10ポイントずつ買って、実行結果だけ日本語で教えて。`
- `毎日1回この市場を見て、YESが指定条件を満たした時だけ10ポイント買って、それ以外は何もしないで。`
- `毎晩、残高とポートフォリオの変化だけ日本語でまとめて。`
- `この市場が終わるまで監視して、終了が近づいたら間隔を詰めて、残り1時間・30分・10分でも知らせて。`

For the complete behavior and scheduling recipes, see `docs/conversation-recipes.md`.

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
