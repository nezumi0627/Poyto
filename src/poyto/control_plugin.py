from __future__ import annotations

import argparse
import hmac
import os
import secrets
from pathlib import Path
from typing import Any

from .control_exec import ExecManager
from .control_fs import ControlPatcher, ControlReader
from .control_paths import ControlPaths
from .mcp_server import build_server as build_poyto_server

_DEFAULT_TOKEN_FILE = "/data/control-plugin.token"
_CONTROL_SCOPE = "poyto:control"


def _token_file(path: str | None = None) -> Path:
    value = path or os.getenv("POYTO_PLUGIN_TOKEN_FILE") or _DEFAULT_TOKEN_FILE
    return Path(value).expanduser()


def ensure_plugin_token(path: str | None = None) -> str:
    explicit = os.getenv("POYTO_PLUGIN_TOKEN")
    if explicit:
        if len(explicit) < 24:
            raise ValueError("POYTO_PLUGIN_TOKEN must contain at least 24 characters")
        return explicit

    target = _token_file(path)
    try:
        token = target.read_text(encoding="utf-8").strip()
    except FileNotFoundError:
        target.parent.mkdir(parents=True, exist_ok=True)
        token = secrets.token_urlsafe(32)
        flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
        fd = os.open(target, flags, 0o600)
        try:
            os.write(fd, (token + "\n").encode())
        finally:
            os.close(fd)
        # The production image uses uid/gid 10001. Host-control mode runs the
        # same image as root, so keep the generated token readable after a
        # later switch back to the unprivileged default mode.
        if os.geteuid() == 0:
            try:
                os.chown(target, 10001, 10001)
            except OSError:
                pass
    if len(token) < 24:
        raise ValueError(f"plugin token in {target} must contain at least 24 characters")
    return token


class StaticTokenVerifier:
    def __init__(self, expected: str) -> None:
        self.expected = expected

    async def verify_token(self, token: str) -> Any:
        if not hmac.compare_digest(token, self.expected):
            return None
        try:
            from mcp.server.auth.provider import AccessToken
        except ImportError as exc:  # pragma: no cover - optional dependency
            raise RuntimeError("MCP support is not installed") from exc
        return AccessToken(
            token=token,
            client_id="poyto-server-control",
            scopes=[_CONTROL_SCOPE],
        )


def _auth_kwargs(token: str) -> dict[str, Any]:
    try:
        from mcp.server.auth.settings import AuthSettings
        from pydantic import AnyHttpUrl
    except ImportError as exc:  # pragma: no cover - optional dependency
        raise RuntimeError("MCP support is not installed") from exc
    issuer = os.getenv("POYTO_PLUGIN_ISSUER_URL", "https://poyto-control.invalid")
    return {
        "token_verifier": StaticTokenVerifier(token),
        "auth": AuthSettings(
            issuer_url=AnyHttpUrl(issuer),
            resource_server_url=None,
            required_scopes=[_CONTROL_SCOPE],
        ),
    }


def build_control_plugin(
    *,
    host: str = "127.0.0.1",
    port: int = 8765,
    token: str | None = None,
    authenticated: bool = True,
) -> Any:
    if not authenticated and host not in {"127.0.0.1", "localhost", "::1"}:
        raise ValueError("Unauthenticated control requires a loopback bind")
    try:
        from mcp.types import ToolAnnotations
    except ImportError as exc:  # pragma: no cover - optional dependency
        raise RuntimeError("MCP support is not installed. Install Poyto with: pip install -e '.[agent]'") from exc

    paths = ControlPaths.from_env()
    auth = _auth_kwargs(token or ensure_plugin_token()) if authenticated else {}
    # Tunnel forwarding must not depend on a sticky HTTP MCP session. Shell
    # session IDs still belong to this server process and survive HTTP requests.
    auth.update(stateless_http=True, json_response=True)
    extra = (
        "This endpoint is the Poyto Server Control plugin. It also exposes Codex-style Linux "
        "server primitives named read, apply_patch, exec_command and write_stdin. File tools "
        f"are confined to these configured roots: {paths.describe_roots()}. exec_command starts "
        "inside an approved root but is intentionally not filesystem-sandboxed after launch, "
        "so callers should treat command access as the authority of the configured container or host mode. "
        f"Command execution mode is {paths.exec_mode!r}. Use the host client's web/search tools "
        "for public Internet research; this plugin is for POYP state and the attached Linux server. "
        "Prefer dedicated Poyto tools. If a Poyto operation has no dedicated tool, use "
        "exec_command to run the installed poyto CLI (poyto --help lists commands). "
        "Authorized CLI mutations require --yes. Shell execution is also a write-capable "
        "tool and does not override the host client's tool permissions. Never print "
        "session files, tokens or private traffic through file or command tools."
    )
    mcp = build_poyto_server(
        host=host,
        port=port,
        read_only=False,
        server_name="Poyto Server Control",
        extra_instructions=extra,
        fastmcp_kwargs=auth,
    )

    reader = ControlReader(paths)
    patcher = ControlPatcher(paths)
    executor = ExecManager(paths)
    read_annotations = ToolAnnotations(
        readOnlyHint=True,
        destructiveHint=False,
        idempotentHint=True,
        openWorldHint=False,
    )
    write_annotations = ToolAnnotations(
        readOnlyHint=False,
        destructiveHint=True,
        idempotentHint=False,
        openWorldHint=True,
    )

    @mcp.tool(annotations=read_annotations)
    def server_info() -> dict[str, Any]:
        """Describe this control plugin's Linux execution mode and approved file roots."""
        return {
            "exec_mode": paths.exec_mode,
            "roots": [str(root) for root in paths.roots],
            "host_root": str(paths.host_root) if paths.exec_mode == "host" else None,
            "uid": os.geteuid(),
            "host_control_ready": (
                paths.exec_mode == "host"
                and os.geteuid() == 0
                and Path("/proc/1/ns/mnt").exists()
            ),
        }

    @mcp.tool(annotations=read_annotations)
    def read(
        paths: list[str],
        start_line: int | None = None,
        end_line: int | None = None,
        max_bytes: int = 256 * 1024,
    ) -> str:
        """Read approved Linux files or list one directory level. Globs are supported and bounded."""
        return reader.read(
            paths,
            start_line=start_line,
            end_line=end_line,
            max_bytes=max_bytes,
        )

    @mcp.tool(annotations=write_annotations)
    def apply_patch(patch: str, workdir: str | None = None) -> str:
        """Apply a Codex-style *** Begin Patch file patch inside approved plugin roots."""
        return patcher.apply_patch(patch, workdir=workdir)

    @mcp.tool(annotations=write_annotations)
    def exec_command(
        cmd: str | None = None,
        cmds: list[str] | None = None,
        workdir: str | None = None,
        tty: bool = False,
        yield_time_ms: int = 10_000,
        max_output_tokens: int = 10_000,
        shell: str | None = None,
    ) -> dict[str, Any]:
        """Run a real Linux shell command; long-running commands return a session_id for write_stdin."""
        return executor.exec_command(
            cmd=cmd,
            cmds=cmds,
            workdir=workdir,
            tty=tty,
            yield_time_ms=yield_time_ms,
            max_output_tokens=max_output_tokens,
            shell=shell,
        )

    @mcp.tool(annotations=write_annotations)
    def write_stdin(
        session_id: int,
        chars: str = "",
        yield_time_ms: int = 5_000,
        max_output_tokens: int = 10_000,
    ) -> dict[str, Any]:
        """Write to or poll a background exec_command session and drain its next output chunk."""
        return executor.write_stdin(
            session_id=session_id,
            chars=chars,
            yield_time_ms=yield_time_ms,
            max_output_tokens=max_output_tokens,
        )

    return mcp


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Expose Poyto plus Linux server control as a standalone MCP app"
    )
    parser.add_argument("--transport", choices=("stdio", "streamable-http"), default="streamable-http")
    parser.add_argument("--host", default=os.getenv("POYTO_PLUGIN_HOST", "127.0.0.1"))
    parser.add_argument("--port", type=int, default=int(os.getenv("POYTO_PLUGIN_PORT", "8765")))
    parser.add_argument(
        "--token-file",
        default=os.getenv("POYTO_PLUGIN_TOKEN_FILE", _DEFAULT_TOKEN_FILE),
        help="Bearer token file. Created with mode 0600 when missing.",
    )
    parser.add_argument(
        "--insecure-no-auth",
        action="store_true",
        help="Disable Bearer authentication; accepted only for a loopback bind.",
    )
    return parser


def main(argv: list[str] | None = None) -> None:
    args = build_parser().parse_args(argv)
    if args.transport == "stdio":
        # The parent process owns the pipes; no network listener or HTTP token
        # is needed, including when tunnel-client launches this process.
        build_control_plugin(authenticated=False).run(transport="stdio")
        return
    loopback = args.host in {"127.0.0.1", "localhost", "::1"}
    if args.insecure_no_auth and not loopback:
        raise SystemExit("--insecure-no-auth is only allowed on a loopback bind")
    token = None if args.insecure_no_auth else ensure_plugin_token(args.token_file)
    server = build_control_plugin(
        host=args.host,
        port=args.port,
        token=token,
        authenticated=not args.insecure_no_auth,
    )
    server.run(transport="streamable-http")


def token_main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Print the Poyto Server Control Bearer token")
    parser.add_argument("--token-file", default=os.getenv("POYTO_PLUGIN_TOKEN_FILE", _DEFAULT_TOKEN_FILE))
    args = parser.parse_args(argv)
    print(ensure_plugin_token(args.token_file))


if __name__ == "__main__":
    main()


__all__ = ["StaticTokenVerifier", "build_control_plugin", "ensure_plugin_token", "main", "token_main"]
