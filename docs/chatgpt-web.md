# ChatGPT Web + Poyto Server Control

Poyto Server Control is a **standalone ChatGPT custom MCP app**. Chat On Steroids is not used at runtime. The implementation borrows the familiar `read`, `apply_patch`, `exec_command`, and `write_stdin` interaction model, but the Docker container itself serves the Streamable HTTP MCP endpoint that ChatGPT connects to.

## Run the Docker app

The image serves MCP at:

```text
http://HOST:8765/mcp
```

For a local/private container:

```bash
docker run -d \
  --name poyto \
  --restart unless-stopped \
  -p 127.0.0.1:8765:8765 \
  -v poyto-data:/data \
  -v /srv/projects:/workspace \
  ghcr.io/tqmane/poyto:latest
```

Docker defaults to:

```text
POYTO_PLUGIN_HOST=0.0.0.0
POYTO_PLUGIN_PORT=8765
POYTO_PLUGIN_TOKEN_FILE=/data/control-plugin.token
POYTO_PLUGIN_ROOTS=/workspace:/data
POYTO_PLUGIN_EXEC_MODE=container
POYTO_SESSION_FILE=/data/session.json
```

The built-in MCP transport requires a random Bearer token by default. It is generated on first start and persisted at `/data/control-plugin.token`:

```bash
docker exec poyto poyto-plugin-token
```

That static token is useful for generic MCP clients and authentication gateways. It is separate from the POYP session credential.

## Connect ChatGPT directly

ChatGPT does not connect directly to a loopback-only MCP server. For a private Linux server, use **OpenAI Secure MCP Tunnel** so the MCP endpoint does not have to be exposed to the public Internet. For an Internet-facing deployment, use an authenticated HTTPS endpoint and a ChatGPT-compatible authentication mechanism such as OAuth.

In ChatGPT developer/custom-app settings, create a custom app and point it at the remote/tunneled `/mcp` endpoint, then scan the tools. No Chat On Steroids connector or intermediary process is required.

For Secure MCP Tunnel on the same Linux server, use the supplied overlay:

```bash
docker compose -f compose.yaml -f compose.secure-tunnel.yaml up -d --build
```

It runs the container with host networking, binds Poyto Server Control only to `127.0.0.1:8765`, and disables the built-in static Bearer token so the tunnel can speak MCP directly. There is no public listener in this mode. Do not use `--insecure-no-auth` with a publicly reachable bind.

The current OpenAI documentation is the authority for the exact UI and supported authentication choices:

- https://help.openai.com/en/articles/12584461
- https://help.openai.com/en/articles/11487775-apps-in-chatgpt

Do not assume that every ChatGPT plan/version can inject an arbitrary static Bearer header from the custom-app UI. If the direct connection path cannot use the built-in static token, terminate authentication in Secure MCP Tunnel or an OAuth-capable gateway rather than publishing the host-control endpoint anonymously.

## ChatGPT plan limitation

As of September 2026, OpenAI documents full custom-MCP write/modify support for Business and Enterprise/Edu. Pro can build apps and connect read/fetch MCP surfaces, but full MCP write actions are not currently documented as available on Pro. This is a ChatGPT product-side restriction; the Poyto server still exposes its write-capable tool schemas correctly.

## Using web research and Poyto together

Poyto deliberately does **not** proxy general web search. The MCP server tells the host model to treat Poyto as the source of POYP account/market state and to use ChatGPT's own web/search capability for current external facts.

A useful workflow is:

1. Call `markets` to discover candidates.
2. Call `market` and `market_activity` for POYP-specific state.
3. Use ChatGPT Web Search for current real-world evidence relevant to the market question.
4. Keep POYP-provided data and external evidence separate in the analysis.
5. Re-fetch the market before a time-sensitive conclusion or mutation.

## Linux server control

Normal Docker mode runs commands inside the Poyto container. `read` and `apply_patch` are limited to configured roots, while `exec_command` is a real shell and can reach anything the container user can reach once launched.

For full host-server administration, run with both compose files:

```bash
docker compose -f compose.yaml -f compose.host-control.yaml up -d --build
```

That mode is root-equivalent: the container joins the host PID namespace, runs privileged, bind-mounts `/` at `/host`, and uses `nsenter` for command execution in the host namespaces. Treat access to this MCP endpoint as root administrative access to the server.

## Authentication boundary

POYP credentials remain in `/data/session.json` and are never MCP tool arguments. Transport authentication is a separate layer. TLS only encrypts traffic; it does not authenticate the caller. Host-control deployments must use a private tunnel or a real authentication/access-control layer.
