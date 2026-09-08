# Examples

## Basic API

- `basic.py` — create a `PoytoClient` and read basic account data.
- `market_snapshot.py` — fetch a compact market snapshot.

## AI-assisted three-trade workflow

- `ai_three_trades.py` — authenticate with a POYP token/session, fetch 10 ending-soon markets, display their details, ask an OpenAI-compatible AI endpoint to compare them, select three candidates using confidence/estimated-edge thresholds, optionally place the three trades, and keep monitoring until all three resolve.

Dry run:

```powershell
$env:POYTO_TOKEN = "..."
$env:POYTO_AI_API_KEY = "..."
$env:POYTO_AI_MODEL = "YOUR_MODEL"
python examples/ai_three_trades.py --points 10
```

Execute the selected three and wait for all results:

```powershell
python examples/ai_three_trades.py --points 10 --execute
```

See [`docs/ai-three-trades.md`](../docs/ai-three-trades.md) for the full workflow, AI JSON contract, thresholds, polling behavior, and risk notes.
