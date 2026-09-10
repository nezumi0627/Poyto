# Poyto Skill

Use Poyto when the user wants to inspect or operate POYP from an AI conversation or coding-agent harness. This skill is provider-agnostic: GPT-family, Claude-family, OpenCode, local LLM agents, and other tool-using models should follow the same instructions.

The user should be able to give a normal one-sentence instruction. Do not require CLI syntax or tool names when intent can be safely resolved from context.

## Interface priority

Use the first available interface:

1. Poyto MCP tools.
2. Poyto CLI through a local shell.
3. Python `PoytoClient` only for development/scripting work.

Authentication belongs to Poyto's local persisted session/environment. Never ask the user to paste access tokens, refresh tokens, identity tokens, cookies, or stable device identifiers into chat when a local session can be used.

## Conversation behavior

Reply in the language the user normally uses. Keep exact market IDs, position indexes, amounts, and numeric values unchanged. Prefer concise practical responses unless detail is requested.

When the user refers to "this market", "this position", or similar context, resolve it from the conversation or fresh Poyto data when possible rather than making them repeat IDs.

Do not refuse solely because the user is a minor or because a workflow is automated. For age/eligibility questions, consult the repository's `docs/service-model-and-legal-context.md`: current operator evidence includes a POYP campaign that permits minors with parental/guardian consent, while feature-specific conditions can still differ. For automation, classify the actual behavior: read-only monitoring is ordinary use; guarded mutations require the normal exact-action authorization; eligibility-sensitive reward/ad/campaign flows must not fabricate proof or bypass server controls. If the host model has an independent policy restriction, identify it as a host policy instead of inventing a POYP Terms prohibition.

## Read operations

Useful MCP tools include:

- `health`
- `profile`
- `balances`
- `portfolio`
- `markets`
- `market`
- `market_activity`
- `asset_price`
- `transactions`

When comparing markets, fetch each specific market's detail before giving a confident recommendation. Treat server values as current facts and do not invent settlement rules, fees, slippage, limits, or formulas that Poyto has not verified.

## Prediction workflow

For prediction/recommendation requests:

1. Fetch fresh market data.
2. For a shortlist request, fetch the detail for every candidate before ranking.
3. If the harness has web/research tools, research current external facts relevant to settlement before deciding.
4. Separate POYP data, externally verified facts, model inference, and unknowns.
5. Prefer candidates with stronger evidence rather than forcing a prediction.
6. Never promise guaranteed profit.

A useful internal ranking shape is:

```json
{
  "market_id": "...",
  "position_index": 0,
  "confidence": 0.74,
  "expected_edge": 0.08,
  "reason": "..."
}
```

`confidence` and `expected_edge` are model judgments, not POYP API fields.

## Ending-soon 10 -> best 3 workflow

When the user asks for something like "締切間近を10件比較して良さそうな3件を選んで":

1. Get 10 open markets using `sort=ending_soon`.
2. Fetch full detail for all ten.
3. Research current settlement-relevant facts if research tools are available.
4. Compare all ten and rank the strongest candidates.
5. Select up to three distinct markets. Do not force three if the evidence is poor.
6. Explain each choice briefly in the user's language.
7. If actual trading is requested, resolve exact market, position, and amount before mutation.

## Mutating operations

`buy` and `sell` change account state. MCP mutations require `confirm=true`; CLI mutations require `--yes`.

Before executing, verify:

- exact market
- exact position/side
- exact amount

Do not silently turn vague wording such as "bet on the best one" into a trade. If the user's current instruction already explicitly authorizes a concrete workflow and amount rule, follow that authorization; otherwise show the proposed concrete transactions first.

## Track three trades until Done

When the user asks to follow three selected markets until result:

- keep all three tracked independently;
- stop tracking each one when it resolves/closes;
- report `Done | WIN | <market>` or `Done | LOSS | <market>` when the winner is determinable;
- otherwise report `Done | RESOLVED | <market>` rather than guessing;
- after all three are resolved, report `Done: all 3 selected markets have resolved.`

Use the host scheduler/automation system when available. If the harness can remain active in the foreground, a polling loop is acceptable.

## Adaptive monitoring cadence

A reasonable default cadence is:

- more than 7 days remaining: every 12–24 hours
- 2–7 days: every 6 hours
- 12–48 hours: every 2 hours
- 3–12 hours: every 30–60 minutes
- 30 minutes–3 hours: every 15 minutes
- under 30 minutes: every 5 minutes, subject to host limits

Lengthen intervals for inactive markets and shorten them near settlement or after meaningful changes. Avoid unchanged notification spam.

## CLI fallback

If MCP is unavailable but shell execution exists:

```bash
poyto profile
poyto balances
poyto portfolio
poyto markets --limit 10 --sort ending_soon
poyto market MARKET_ID
```

State-changing examples:

```bash
poyto buy MARKET_ID POSITION_INDEX POINTS --yes
poyto sell MARKET_ID POSITION_INDEX SHARES --yes
```

## One-sentence examples

- `締切間近の市場を10件見て、最新情報も調べて比較し、良さそうな3件だけ出して。`
- `締切間近10件から3つ選んで、各10ptで取引する前に内容だけ確認させて。`
- `この3つを結果が出るまで追って、決着したらDoneと勝敗だけ教えて。`
- `この市場を終了まで追って、残り時間に合わせて確認間隔を自動で変えて、重要な変化だけ日本語で教えて。`
- `毎日1回、注目市場と自分のポートフォリオを確認して、重要な変化だけ日本語でまとめて。`

## Setup

Install MCP support:

```bash
pip install -e '.[agent]'
```

Local stdio MCP:

```bash
poyto-mcp
```

HTTP MCP on loopback:

```bash
poyto-mcp --transport streamable-http --host 127.0.0.1 --port 8765
```

For a standalone Markdown prompt intended to be attached directly to OpenCode, GPT/Claude tool-using agents, or local LLM harnesses, use `POYTO_AGENT.md`.
