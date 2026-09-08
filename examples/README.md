# Examples

## Basic API

- `basic.py` — create a `PoytoClient` and read basic account data.
- `market_snapshot.py` — fetch a compact market snapshot.

AI/model integration intentionally does not live in `examples/` as provider-specific application code. To operate Poyto from GPT-family, Claude-family, OpenCode, local LLM agents, or another tool-using harness, attach [`POYTO_AGENT.md`](../POYTO_AGENT.md) or [`skills/poyto/SKILL.md`](../skills/poyto/SKILL.md) and expose the Poyto MCP server or CLI to the harness.
