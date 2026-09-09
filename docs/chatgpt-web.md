# ChatGPT Web + Poyto Server Control

For a fresh install on another Linux machine, follow the [日本語セットアップ手順](setup-ja.md), including session migration, tunnel registration, service management and the Docker alternative.

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

## Connect ChatGPT through Secure MCP Tunnel

Yes: use [Platform → Tunnels](https://platform.openai.com/settings/organization/tunnels).
The connection is `ChatGPT → Secure MCP Tunnel → Poyto Server Control → PoytoClient/CLI`.
It needs no Chat On Steroids runtime or Chrome extension.

### 1. Prepare Poyto

For this Linux checkout, the simplest setup uses stdio. The tunnel starts Poyto
as a subprocess, so no HTTP port or plugin Bearer token is needed:

```bash
python3 -m venv .venv
.venv/bin/pip install -e '.[agent]'
```

The absolute launch command is `bash /absolute/path/to/Poyto/scripts/run-plugin-stdio.sh`.
That script selects the checkout's virtual environment and defaults file access
roots to the checkout. Set `POYTO_PLUGIN_ROOTS` to change those roots. On a native
host, shell commands run as the logged-in OS user; the internal `container` mode
name means ordinary execution without `nsenter`, not an automatic sandbox.

Import your authorized POYP session locally using [authentication setup](authentication.md).
Existing saved credentials are loaded normally. To use another saved session,
prefix the profile's command with `env POYTO_SESSION_FILE=/absolute/private/path/session.json`.
Poyto reads and persists rotated credentials at that same path; keep one session
store per active client/process where possible. The connection smoke test below
needs no POYP credentials and does not submit account operations.

Alternatively, for Docker HTTP on the same Linux host:

```bash
docker compose -f compose.yaml -f compose.secure-tunnel.yaml up -d --build
```

This binds `127.0.0.1:8765/mcp` with no static Bearer token. The tunnel is the
intended ingress. `POYTO_PLUGIN_TUNNEL_PORT` changes both the listener and Docker
health-check port. This overlay starts Poyto only; run `tunnel-client` separately.
Do not use anonymous HTTP on a public interface.

### 2. Prepare the tunnel

Create a dedicated tunnel in Platform settings, associate it with the target
ChatGPT workspace, and keep its `tunnel_id`. Creating/editing requires Tunnels
**Read + Manage**; running the client and choosing the tunnel require
**Read + Use**. Create a restricted runtime key with those runtime permissions.
The POYP session and tunnel key are separate credentials.

Download `tunnel-client` from the Platform page or the
[official latest release](https://github.com/openai/tunnel-client/releases/latest).
Run `tunnel-client help quickstart` to check the installed client's commands.
Enter the runtime key locally without echoing it or including it in shell history:

```bash
read -rsp 'Tunnel runtime key: ' CONTROL_PLANE_API_KEY
export CONTROL_PLANE_API_KEY
```

Configure a dedicated stdio profile once (replace the synthetic ID and absolute path):

```bash
tunnel-client init \
  --sample sample_mcp_stdio_local \
  --profile poyto \
  --tunnel-id tunnel_0123456789abcdef0123456789abcdef \
  --mcp-command "bash /absolute/path/to/Poyto/scripts/run-plugin-stdio.sh"
tunnel-client doctor --profile poyto --explain
tunnel-client run --profile poyto
```

For Docker HTTP, use this profile instead:

```bash
tunnel-client init \
  --sample sample_mcp_remote_no_auth \
  --profile poyto-http \
  --tunnel-id tunnel_0123456789abcdef0123456789abcdef \
  --mcp-server-url http://127.0.0.1:8765/mcp
```

Run doctor/run with `--profile poyto-http`. The MCP transport uses stateless JSON HTTP responses;
background shell session IDs still live in the Poyto server process.

Keep the client running for discovery and every ChatGPT call. For persistent
service management, the official client's managed runtime can store a file
reference to the key and keep the process alive beyond the terminal:

```bash
tunnel-client runtimes connect \
  --alias poyto --profile poyto \
  --tunnel-id tunnel_0123456789abcdef0123456789abcdef \
  --runtime-api-key file:/absolute/private/path/runtime.key \
  --mcp-command "bash /absolute/path/to/Poyto/scripts/run-plugin-stdio.sh"
tunnel-client runtimes status poyto --json
```

Keep that key file outside the repo with mode `0600`. Check `process_running`,
`healthy`, and `ready`; a launched process alone is not a verified connection.
Managed process mode does not itself establish reboot autostart.
A stopped or disconnected client cannot receive ChatGPT requests.

### 3. Register in ChatGPT Web

1. Enable **Settings → Security and login → Developer mode**.
2. Open [ChatGPT Plugins](https://chatgpt.com/plugins), then select **+**.
3. Name it **Poyto Server Control**. Suggested description:
   “Inspect POYP accounts and markets, perform authorized POYP operations, and run local commands through Poyto.”
4. Under **Connection**, choose **Tunnel** and select the dedicated tunnel (or enter its ID).
5. For this stdio/loopback setup, choose **No Authentication** for MCP; the Secure MCP Tunnel authenticates access. Review the discovered tools and create the connection.
6. Start a conversation, select Developer mode and enable Poyto.

Use the tunnel ID in the **Tunnel** field, not a made-up public MCP URL. If the
tunnel is missing, check its ChatGPT workspace association and Read + Use access.
After changing tool schemas or descriptions, restart Poyto and **Refresh** the
connection metadata before testing a new conversation.

### 4. Verify a real operation

First request:

> Poyto の server_info を実行して、接続先と操作できるディレクトリを教えて。

Then authorize a harmless file operation in an approved root:

> poyto-smoke.txt に connected と書き込んで、読み戻して確認して。

This should use `apply_patch` or `exec_command`, followed by `read`. After local
session setup, ask for `balances` and `portfolio`. For commands without a dedicated
MCP wrapper, the shell can run `poyto --help` and the corresponding CLI operation.
Account mutations retain `confirm=true` / CLI `--yes` and the user's authorization.
Do not paste credentials or request session-file contents in chat.

## Write support and packaging scope

Checked 2026-09-09: the official [Developer mode guide](https://developers.openai.com/api/docs/guides/developer-mode)
describes read and write MCP tools, and lists Pro, Plus, Business, Enterprise and
Education web accounts. Actual availability and confirmations depend on workspace
policy and account settings; an earlier blanket “Pro is read/fetch only” statement
in this repository is no longer supported by that guide.

`exec_command`, `write_stdin` and `apply_patch` are correctly marked as write-capable.
Shell execution is a fallback for missing dedicated tools when execution is
available, not a way to relabel writes as reads or override host permissions.

A private developer-mode connection is enough to use Poyto in ChatGPT Web. A
local `.codex-plugin/plugin.json` plus the bundled Poyto skill can also package
it for a local plugin host; installing that local package alone does not register
the Web connection. After Web registration, its real `plugin_asdk_app...` ID can
be wired into an `.app.json` package. Do not invent that ID.

Secure MCP Tunnel supports private/developer-mode connections, not public plugin
submission. Public distribution has separate endpoint and review requirements.
See [Secure MCP Tunnel](https://developers.openai.com/api/docs/guides/secure-mcp-tunnels)
and [plugin packaging](https://developers.openai.com/plugins/build/plugins).

## Verification boundary

Offline tests exercise MCP initialization, tool discovery, real local file edits,
shell execution, HTTP authentication and confirmation rejection with synthetic
inputs. They establish local implementation behavior only. They do not establish
a connection from your ChatGPT workspace, a healthy OpenAI tunnel, or new POYP API
behavior. Complete the Web smoke test above after registering the connection.

### Live integration check (2026-09-09)

One authorized ChatGPT Web workspace successfully discovered and connected the
plugin through Secure MCP Tunnel. A conversation called `server_info`, ran
`poyto --help` through `exec_command`, created a synthetic test file, and read
it back through `read`. After pointing the tunnel subprocess at an authorized
saved POYP session, `balances` succeeded from that conversation. This establishes
that tested integration only; no account mutation or new POYP route was tested.
Private workspace IDs, tunnel IDs, account values and credentials are omitted.

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

POYP credentials remain in the configured local session file (`/data/session.json` in Docker) and are never MCP tool arguments. Transport authentication is a separate layer. TLS only encrypts traffic; it does not authenticate the caller. Host-control deployments must use a private tunnel or a real authentication/access-control layer.
