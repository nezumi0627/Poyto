# ChatGPT Web + Poyto MCP

Poyto can run as a Streamable HTTP MCP server for ChatGPT and other remote MCP clients. The recommended remote configuration is **read-only by default**: ChatGPT can inspect the user's POYP state and markets while the host chat uses its own web-search capability for current external evidence.

## Run the MCP server

The Docker image starts Streamable HTTP MCP on port `8765` and exposes the MCP endpoint at:

```text
http://HOST:8765/mcp
```

For a local container:

```bash
docker run -d \
  --name poyto \
  --restart unless-stopped \
  -p 127.0.0.1:8765:8765 \
  -v poyto-data:/data \
  ghcr.io/tqmane/poyto:latest
```

Docker defaults to:

```text
POYTO_MCP_TRANSPORT=streamable-http
POYTO_MCP_READ_ONLY=true
POYTO_SESSION_FILE=/data/session.json
```

To expose the full mutation tool set for an MCP client that supports it, explicitly opt in:

```bash
-e POYTO_MCP_READ_ONLY=false
```

The mutation tools still require `confirm=true` and should only be used after explicit confirmation of the exact operation.

## ChatGPT Web

ChatGPT Web does not connect directly to a loopback-only MCP server. Give ChatGPT a remote HTTPS MCP endpoint, or use OpenAI's Secure MCP Tunnel when it is available for the account/workspace. Do not expose a Poyto MCP endpoint containing an authenticated POYP session to the public internet without an authentication/access-control layer.

Current OpenAI documentation says custom MCP apps are configured from ChatGPT developer mode by providing the MCP endpoint, scanning tools, and completing the configured authentication flow when applicable. Search/fetch-named tools are no longer mandatory. See:

- https://help.openai.com/en/articles/12584461
- https://help.openai.com/en/articles/11487775-apps-in-chatgpt

For ChatGPT Pro, the current documented custom-MCP surface is read/fetch-oriented. Full write/modify MCP support is currently documented for Business and Enterprise/Edu. That is why the published Poyto container defaults to read-only mode.

## Using web research and Poyto together

Poyto deliberately does **not** proxy general web search. The MCP server tells the host model to treat Poyto as the source of POYP account/market state, and to use the host's native web/search tools for current external facts when available.

A useful workflow is:

1. Call `markets` to discover candidates.
2. Call `market` and `market_activity` for the POYP-specific state.
3. Use the host chat's web search for current real-world evidence relevant to the market question.
4. Keep POYP-provided data and external web evidence separate in the analysis.
5. Re-fetch the market before making a time-sensitive conclusion.

Read-only MCP tools currently include account/balance/portfolio reads, market/detail/activity reads, asset price, transactions, login bonus, notification count, discovery/home configuration, campaign banners, interest subcategories and loss-gacha status.

## Authentication boundary

POYP credentials remain in Poyto's persisted session file and are never MCP tool arguments. For remote deployment, protect the MCP transport separately as well: TLS alone encrypts traffic but does not authenticate the caller. Use a ChatGPT-compatible authentication mechanism or a supported private tunnel/access layer.
