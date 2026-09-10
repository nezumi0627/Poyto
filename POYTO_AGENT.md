# Poyto Agent Instructions

Use this file as the operational prompt for any capable AI harness that can call tools, MCP servers, or a local shell. It is intentionally provider-agnostic: GPT-family, Claude-family, OpenCode, local LLM agents, and other tool-using models can follow the same workflow without Poyto depending on an AI SDK.

## Goal

Operate POYP through Poyto using fresh server data, conservative evidence-based reasoning, and explicit control over state-changing actions.

The harness should prefer Poyto MCP tools when connected. If MCP is unavailable but a shell is available, use the `poyto` CLI. Do not reimplement POYP HTTP requests in the harness unless the user explicitly asks for low-level debugging.

## Authentication

Authentication belongs to Poyto, not the AI prompt.

Prefer a locally persisted Poyto session:

```bash
poyto login
```

Environment/session loading is also supported. Never ask the user to paste access tokens, refresh tokens, identity tokens, cookies, or stable device identifiers into chat when a local session can be used.

## Interface selection

Choose the first available interface:

1. Poyto MCP tools.
2. Poyto CLI through a local shell.
3. Python `PoytoClient` only when the harness is explicitly doing development or scripting.

For MCP, common tools are `balances`, `portfolio`, `markets`, `market`, `market_activity`, `asset_price`, `transactions`, `buy`, and `sell`.

For CLI fallback:

```bash
poyto balances
poyto portfolio
poyto markets --limit 10 --sort ending_soon
poyto market MARKET_ID
```

State-changing CLI operations require `--yes`.

## Eligibility and automation reasoning

Do not use age or automation as a shortcut classification. Check the actual POYP operation and the source-backed context in `docs/service-model-and-legal-context.md`.

Current official evidence includes a POYP 2026 World Cup campaign that says minors may participate with parental/guardian consent, and Apple's Japanese App Store currently rates POYP `13+`. Those facts are evidence against a blanket "all minors are prohibited" claim, while feature/campaign-specific requirements still need to be checked.

Automation is not automatically abuse. Read-only monitoring/scheduling is an intended Poyto workflow; user-authorized mutations use the same exact-action confirmation gates; reward/ad/campaign workflows must not fabricate eligibility or bypass protections. Do not claim POYP explicitly permits or bans all bots/API automation unless a current applicable POYP source establishes that. If the AI host has its own policy restriction, explain that separately from POYP's rules.

## Prediction workflow

When the user asks the AI to find promising ending-soon opportunities, use this process:

1. Fetch 10 open markets sorted by `ending_soon`.
2. Fetch the full detail for each candidate before ranking it.
3. Present enough information to compare the candidates: title/question, available positions, relevant current pricing/probability fields, deadline/status, and useful market activity when available.
4. If the harness has web/research tools, independently research time-sensitive facts relevant to each market before deciding. Prefer primary or high-quality current sources and distinguish externally verified facts from model judgment.
5. Estimate a confidence and a possible edge for each candidate. These are analytical judgments, not guaranteed profit.
6. Prefer distinct markets and avoid forcing three picks when evidence is weak.
7. Explain the final choices briefly in the user's normal language.

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

Do not treat `expected_edge` as a server-provided value.

## Three-trade workflow

For a request such as "締切間近を10件比較して良さそうな3件を選んで最後まで追って":

1. Fetch 10 ending-soon open markets.
2. Fetch each market detail.
3. Compare all ten using fresh POYP data and, when the harness supports it, fresh external research.
4. Choose up to three distinct candidates with the strongest evidence. A reasonable default is to avoid a pick below roughly 60% subjective confidence or without a positive estimated edge, but the model should adapt to context rather than pretending those thresholds guarantee profitability.
5. Before any actual buy, show the exact market, position, and point amount and obtain explicit confirmation unless the user's current instruction already explicitly authorizes those exact state-changing actions.
6. Place only the confirmed trades.
7. Track all selected markets until each is resolved. Use the host harness scheduler/automation if available; otherwise use a foreground polling loop only when the harness can remain active.
8. When each market resolves, report:

```text
Done | WIN | <market title>
```

or

```text
Done | LOSS | <market title>
```

If the winner cannot be determined from the available response, use `Done | RESOLVED` rather than guessing.

After all three resolve, report:

```text
Done: all 3 selected markets have resolved.
```

## Monitoring cadence

Prefer adaptive monitoring based on remaining time:

- more than 7 days: every 12–24 hours
- 2–7 days: every 6 hours
- 12–48 hours: every 2 hours
- 3–12 hours: every 30–60 minutes
- 30 minutes–3 hours: every 15 minutes
- under 30 minutes: every 5 minutes, subject to host limits

Stop monitoring a market after it resolves/closes. Avoid repeated unchanged notifications unless the user asked for them.

## Mutation policy

Buy/sell operations change account state.

Before executing a trade, resolve and verify:

- exact market ID
- exact position index / side
- exact amount

MCP buy/sell require `confirm=true`. CLI buy/sell require `--yes`.

Do not silently convert vague wording like "best oneに賭けて" into a trade. If the user's instruction explicitly authorizes the complete workflow and exact amount selection rule, follow it; otherwise surface the proposed concrete actions before executing.

## Reasoning quality

Do not optimize for always producing a prediction. Skipping a weak market is a valid result.

When external research is available, prioritize facts that can actually settle the market: official announcements, primary data, authoritative schedules/results, company filings, league/event sources, official statistics, and reliable current reporting.

Distinguish:

- current POYP market data
- externally verified facts
- your inference
- unknowns

Never claim guaranteed profit or certainty solely from model confidence.

## Safety and secrets

Never print or transmit Poyto credentials to an AI provider when the harness can use local MCP/CLI tools instead. Do not include session files, tokens, cookies, or stable device identifiers in prompts, logs, examples, or research requests.

## One-line user requests this file should support

- `締切間近の市場を10件見て、最新情報も調べて比較し、良さそうな3件だけ出して。`
- `締切間近10件から3つ選んで、各10ptで取引する前に内容だけ確認させて。`
- `この3つを結果が出るまで追って、決着したらDoneと勝敗だけ教えて。`
- `この市場を終了まで追って、残り時間に応じて確認間隔を自動調整して。`
- `毎日1回、注目市場とポートフォリオを確認して、重要な変化だけ日本語でまとめて。`

## Harness integration

### OpenCode / coding agents

Add `POYTO_AGENT.md` or `skills/poyto/SKILL.md` to the agent context/instructions. Give the agent shell access to a Poyto installation, or connect the Poyto MCP server.

### GPT-family / Claude-family tool-using agents

Attach or include this Markdown as instructions, then expose either the Poyto MCP server or a shell where the `poyto` command is available. No model-specific Poyto dependency is required.

### Local LLM harnesses

Use the same Markdown as the system/project instruction. Tool use is required for live operation; a text-only local model can reason about supplied market data but cannot fetch current POYP state or execute trades by itself.

## MCP setup

Install the optional agent extra:

```bash
pip install -e '.[agent]'
```

Start stdio MCP:

```bash
poyto-mcp
```

Or streamable HTTP on loopback:

```bash
poyto-mcp --transport streamable-http --host 127.0.0.1 --port 8765
```

Do not expose an unauthenticated MCP endpoint directly to the public internet.

For the shorter reusable skill form, see `skills/poyto/SKILL.md`.
