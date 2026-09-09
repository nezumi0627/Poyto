# Poyto Server Control plugin

`poyto-plugin` packages Poyto's POYP tools and a small Linux command bridge behind one standalone MCP server (Streamable HTTP or stdio). It can be registered directly as a ChatGPT custom MCP app; Chat On Steroids is not required.

## Tool model

The server exposes the normal Poyto account/market/mutation tools plus:

- `server_info` — reports command mode and approved roots without secrets
- `read` — bounded text reads, one-level directory listing and bounded glob expansion
- `apply_patch` — Codex-style `*** Begin Patch` file changes under approved roots
- `exec_command` — real shell commands, single or batched
- `write_stdin` — interactive/background continuation for `exec_command`

The names and interaction model intentionally follow familiar Codex/Chat On Steroids Core conventions so the model does not need a novel terminal abstraction. This is an implementation reference only, not a runtime dependency.

## Local stdio / tunnel subprocess

`poyto-plugin --transport stdio` exposes the same account, file and shell tools
through the parent process's pipes. It opens no HTTP listener and does not create
an HTTP Bearer token. From a source checkout, use
`bash /absolute/path/to/Poyto/scripts/run-plugin-stdio.sh` after installing
`.[agent]` in `.venv`. The launcher defaults approved file roots to that checkout.
Native commands run with the launching user's permissions.

For the full Tunnel ID, runtime key, profile and ChatGPT registration procedure,
see [ChatGPT Web setup](chatgpt-web.md). Local plugin installation and Web
registration are separate steps.

## Authentication

HTTP mode requires a static Bearer token unless explicitly configured for loopback-only tunnel access. Anonymous public binds are rejected by both the CLI and server builder. If `POYTO_PLUGIN_TOKEN` is unset, `poyto-plugin` creates a random token in `POYTO_PLUGIN_TOKEN_FILE` (default `/data/control-plugin.token`) with mode `0600`.

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

HTTP responses are stateless JSON for tunnel forwarding; shell sessions remain process-local. Restarting the server loses those sessions. The command environment excludes `CONTROL_PLANE_API_KEY` as well as the other connector keys. This is not a filesystem or process-isolation boundary.
