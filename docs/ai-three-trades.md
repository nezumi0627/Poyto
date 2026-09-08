# AI-assisted three-trade example

`examples/ai_three_trades.py` demonstrates a complete long-running prediction workflow:

```text
POYP token/session
  -> fetch 10 open markets sorted by ending_soon
  -> fetch each market detail
  -> print the candidate information
  -> send the 10 sanitized market payloads to an OpenAI-compatible AI endpoint
  -> rank by estimated edge + confidence
  -> keep exactly 3 distinct candidates that pass thresholds
  -> optionally place 3 buys
  -> keep the process alive and poll all 3 markets
  -> print Done for each resolved market
  -> exit after all 3 are Done
```

The example tries to select favorable candidates; it does not and cannot guarantee profit.

## AI configuration

The AI endpoint must support the OpenAI-compatible `POST /chat/completions` shape.

Set:

```powershell
$env:POYTO_AI_API_KEY = "..."
$env:POYTO_AI_MODEL = "YOUR_MODEL"
$env:POYTO_AI_BASE_URL = "https://api.openai.com/v1"
```

`POYTO_AI_BASE_URL` can point at another compatible provider or a local compatible server.

Only selected market fields are sent to the AI. Poyto access/refresh tokens and account credentials are not included in the AI prompt.

## POYP authentication

Use a token directly:

```powershell
python examples/ai_three_trades.py --token "YOUR_POYP_ACCESS_TOKEN"
```

Or use normal Poyto session/environment loading:

```powershell
$env:POYTO_TOKEN = "YOUR_POYP_ACCESS_TOKEN"
python examples/ai_three_trades.py
```

A previously persisted Poyto session also works when no explicit token is passed.

## Analysis-only run

The default is a dry run. It fetches and prints the ending-soon candidates, asks the AI to compare them, and prints the selected three without placing orders:

```powershell
python examples/ai_three_trades.py --points 10
```

The default filters are:

```text
minimum AI confidence: 60%
minimum estimated edge: +2%
points per selected trade: 10
```

If three candidates do not pass the thresholds, the script stops instead of forcing weak trades.

Tune them explicitly when needed:

```powershell
python examples/ai_three_trades.py --min-confidence 0.70 --min-edge 0.05
```

## Execute and monitor all three

`--execute` is the explicit switch that enables the three buy operations:

```powershell
python examples/ai_three_trades.py --points 10 --execute
```

After the three buys are submitted, the same process remains alive. It polls each selected market every 60 seconds by default.

As markets resolve, output looks like:

```text
Done | WIN | <market title> | selected=1 | winner=1
Done | LOSS | <market title> | selected=0 | winner=1
Done | WIN | <market title> | selected=1 | winner=1

Done: all 3 selected markets have resolved.
```

Change the polling interval with:

```powershell
python examples/ai_three_trades.py --execute --poll-seconds 120
```

The minimum interval is 10 seconds to avoid accidental aggressive polling.

## Selection logic

The AI is asked to return, for each candidate:

```json
{
  "market_id": "...",
  "position_index": 0,
  "confidence": 0.74,
  "expected_edge": 0.08,
  "reason": "..."
}
```

The script then validates the IDs and position indexes, rejects duplicate markets, applies the configured confidence/edge thresholds, sorts by estimated edge and confidence, and keeps three candidates.

`expected_edge` is an AI estimate. It is not an API-provided expected return and is not a promise of profit.

## What the AI sees

The example deliberately strips the market payload down to useful market data such as title/question, description/summary, positions/outcomes, phase/status, deadline fields, volume and liquidity when present.

It does not send POYP credentials or unrelated account metadata.

By default the AI reasons over the POYP market data supplied to it. If a stronger research process is required, use an AI/agent stack that can enrich the candidate information with current external sources before ranking, while keeping the same three-pick JSON contract.

## Long-running behavior

Transient errors while checking a market do not immediately terminate the watcher. The error is printed and the next polling cycle retries it.

The process exits only when all three selected markets are recognized as resolved/closed/settled, or when the user stops the process.

Because POYP is undocumented, settlement field names can change. The watcher checks several common response fields and should be updated if the service response shape changes.

## Risk and responsibility

Prediction quality depends on model quality, available information, market pricing, timing, and server behavior. AI confidence can be wrong. Use small point amounts first and inspect dry-run output before enabling `--execute`.

See [`DISCLAIMER.md`](../DISCLAIMER.md) and [`known-gaps.md`](known-gaps.md).
