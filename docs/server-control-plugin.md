# Poyto Server Control plugin

`poyto-plugin` packages Poyto's POYP tools and a small Linux command bridge behind one standalone Streamable HTTP MCP endpoint. It can be registered directly as a ChatGPT custom MCP app; Chat On Steroids is not required.

## Tool model

The server exposes the normal Poyto account/market/mutation tools plus:

- `server_info` — reports command mode and approved roots without secrets
- `read` — bounded text reads, one-level directory listing and bounded glob expansion
- `apply_patch` — Codex-style `*** Begin Patch` file changes under approved roots
- `exec_command` — real shell commands, single or batched
- `write_stdin` — interactive/background continuation for `exec_command`

The names and interaction model intentionally follow familiar Codex/Chat On Steroids Core conventions so the model does not need a novel terminal abstraction. This is an implementation reference only, not a runtime dependency.

## Authentication

HTTP mode requires a static Bearer token. If `POYTO_PLUGIN_TOKEN` is unset, `poyto-plugin` creates a random token in `POYTO_PLUGIN_TOKEN_FILE` (default `/data/control-plugin.token`) with mode `0600`.

Print it only when configuring the client:

```bash
docker compose exec poyto poyto-plugin-token
```

The static Bearer token is suitable for generic MCP clients and authentication gateways. For direct ChatGPT Web use, prefer OpenAI Secure MCP Tunnel for a private/on-prem server or put the endpoint behind a ChatGPT-compatible OAuth/authentication layer. Do not assume the ChatGPT custom-app UI can inject this static token on every plan/version.

For Secure MCP Tunnel running on the same Linux host, use:

```bash
docker compose -f compose.yaml -f compose.secure-tunnel.yaml up -d --build
```

That overlay switches to host networking, removes the published Docker port, binds MCP to `127.0.0.1:8765`, and starts `poyto-plugin --insecure-no-auth`. The lack of an application-layer token is intentional only because the endpoint is loopback-only and the Secure MCP Tunnel is the access path.

## Container mode

Default:

```text
POYTO_PLUGIN_EXEC_MODE=container
POYTO_PLUGIN_ROOTS=/workspace:/data
```

File tools cannot resolve outside those roots, including through symlink escapes. `exec_command` must start in an approved root, but the command itself is not a filesystem sandbox. It runs with the normal container user's permissions.

## Full host-control mode

Run:

```bash
docker compose -f compose.yaml -f compose.host-control.yaml up -d --build
```

The overlay deliberately enables:

```text
user: 0:0
privileged: true
pid: host
/:/host:rw,rslave
POYTO_PLUGIN_EXEC_MODE=host
POYTO_PLUGIN_ROOTS=/host:/data
```

In this mode `exec_command` uses `nsenter` into PID 1's mount/UTS/IPC/network/PID namespaces and maps a workdir under `/host/...` back to its host path. This is intentionally equivalent to granting root administration of the Linux server. Do not use this overlay merely to access project files; bind only the required project directories into `/workspace` instead.

## Runtime separation

Android, ADB and Frida are development-time verification tools only. The production/server Docker image has no dependency on a connected Android device.
