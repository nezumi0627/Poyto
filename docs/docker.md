# Docker

Poyto includes a small Docker image for the MCP server. The default container is intentionally conservative: it runs as an unprivileged user, stores only the Poyto session under `/data`, defaults MCP to read-only mode, and does not receive the Docker socket or host-root mounts.

## Build and run

```bash
docker compose up -d --build
docker compose ps
```

The compose file publishes MCP only on loopback:

```text
http://127.0.0.1:8765/mcp
```

Change the host-side port with `POYTO_MCP_PUBLISH_PORT` if needed.

## Session

The container uses:

```text
POYTO_SESSION_FILE=/data/session.json
```

Import or copy an authorized Poyto session into the `poyto-data` volume without exposing its contents in chat, Git, logs, or Compose environment variables.

## Mutations

The Docker image defaults to:

```text
POYTO_MCP_READ_ONLY=true
```

Only disable read-only mode when the MCP endpoint is behind a trusted transport and you intentionally want account-changing tools. Individual mutation tools still require `confirm=true`.

## Remote access

Do not change the published bind from `127.0.0.1` to a public interface as a shortcut. For ChatGPT or another remote MCP host, use a supported private tunnel or authenticated HTTPS MCP gateway. Transport authentication and POYP account authentication are separate concerns.

## What this image does not do

The default Poyto image does not expose shell execution, arbitrary host filesystem access, the Docker socket, privileged mode, host PID/network namespaces, `nsenter`, or a writable host-root mount. Those capabilities are server administration, not POYP API functionality, and intentionally remain outside the default MCP trust boundary.
