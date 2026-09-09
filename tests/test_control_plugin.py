from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Any

import httpx
import pytest
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

from poyto.control_exec import ExecManager, _child_environment
from poyto.control_fs import ControlPatcher, ControlReader
from poyto.control_paths import ControlPathError, ControlPaths
from poyto.control_plugin import build_control_plugin, ensure_plugin_token, main


def _paths(monkeypatch: pytest.MonkeyPatch, root: Path) -> ControlPaths:
    monkeypatch.setenv("POYTO_PLUGIN_ROOTS", str(root))
    monkeypatch.setenv("POYTO_PLUGIN_EXEC_MODE", "container")
    return ControlPaths.from_env()


def _finish(manager: ExecManager, result: dict[str, Any]) -> dict[str, Any]:
    """Collect yielded output without assuming how fast a CI runner starts a shell."""
    output = result["output"]
    for _ in range(10):
        if "exit_code" in result:
            return {**result, "output": output}
        result = manager.write_stdin(session_id=result["session_id"], yield_time_ms=1000)
        output += result["output"]
    pytest.fail("command did not finish within the bounded polling window")


def test_control_reader_and_patch_are_root_scoped(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    paths = _paths(monkeypatch, tmp_path)
    target = tmp_path / "hello.txt"
    target.write_text("one\ntwo\n", encoding="utf-8")

    reader = ControlReader(paths)
    rendered = reader.read([str(target)])
    assert "1\tone" in rendered
    assert "2\ttwo" in rendered

    patcher = ControlPatcher(paths)
    result = patcher.apply_patch(
        """*** Begin Patch
*** Update File: hello.txt
@@
 one
-two
+three
*** Add File: added.txt
+created
*** End Patch""",
        workdir=str(tmp_path),
    )
    assert "Updated: hello.txt" in result
    assert "Added: added.txt" in result
    assert target.read_text(encoding="utf-8") == "one\nthree\n"
    assert (tmp_path / "added.txt").read_text(encoding="utf-8") == "created\n"


def test_control_paths_reject_symlink_escape(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    root = tmp_path / "root"
    outside = tmp_path / "outside"
    root.mkdir()
    outside.mkdir()
    (outside / "secret.txt").write_text("secret", encoding="utf-8")
    (root / "escape").symlink_to(outside, target_is_directory=True)
    paths = _paths(monkeypatch, root)

    with pytest.raises(ControlPathError):
        paths.resolve_existing(root / "escape" / "secret.txt")


def test_exec_command_and_write_stdin(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    manager = ExecManager(_paths(monkeypatch, tmp_path))
    try:
        immediate = _finish(manager, manager.exec_command(
            cmd="printf hello", workdir=str(tmp_path), yield_time_ms=0,
        ))
        assert immediate["exit_code"] == 0
        assert immediate["output"] == "hello"

        # Waiting for stdin guarantees a running session without a sleep/race.
        background = manager.exec_command(
            cmd='read -r value; printf "%s" "$value"',
            workdir=str(tmp_path),
            yield_time_ms=0,
        )
        assert "session_id" in background
        final = _finish(manager, manager.write_stdin(
            session_id=background["session_id"], chars="done\n", yield_time_ms=0,
        ))
        assert final["exit_code"] == 0
        assert final["output"] == "done"
    finally:
        manager.close()


def test_exec_batch_keeps_first_nonzero_exit_and_continues(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    manager = ExecManager(_paths(monkeypatch, tmp_path))
    try:
        result = _finish(manager, manager.exec_command(
            cmds=["export POYTO_TEST_VALUE=works", "false", "printf \"$POYTO_TEST_VALUE\""],
            workdir=str(tmp_path),
            yield_time_ms=0,
        ))
        assert result["exit_code"] == 1
        assert "works" in result["output"]
        assert "command 3/3" in result["output"]
    finally:
        manager.close()


def test_plugin_token_is_created_private(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("POYTO_PLUGIN_TOKEN", raising=False)
    path = tmp_path / "plugin.token"
    token = ensure_plugin_token(str(path))
    assert len(token) >= 24
    assert ensure_plugin_token(str(path)) == token
    assert os.stat(path).st_mode & 0o777 == 0o600


@pytest.mark.anyio
async def test_control_plugin_exposes_poyto_and_core_tools(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _paths(monkeypatch, tmp_path)
    server = build_control_plugin(authenticated=False)
    tools = {tool.name: tool for tool in await server.list_tools()}
    assert {"markets", "buy", "sell", "read", "apply_patch", "exec_command", "write_stdin"} <= tools.keys()
    assert tools["read"].annotations and tools["read"].annotations.readOnlyHint is True
    assert tools["exec_command"].annotations and tools["exec_command"].annotations.readOnlyHint is False
    assert tools["buy"].annotations and tools["buy"].annotations.readOnlyHint is False


def test_tunnel_key_is_not_in_command_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("CONTROL_PLANE_API_KEY", "synthetic-tunnel-key")
    assert "CONTROL_PLANE_API_KEY" not in _child_environment()


@pytest.mark.parametrize("host", ["0.0.0.0", "::", "192.0.2.1"])
def test_builder_rejects_anonymous_public_listener(host: str) -> None:
    with pytest.raises(ValueError, match="loopback"):
        build_control_plugin(host=host, authenticated=False)


def test_cli_rejects_anonymous_public_listener() -> None:
    with pytest.raises(SystemExit, match="loopback"):
        main(["--host", "0.0.0.0", "--insecure-no-auth"])


@pytest.mark.anyio
async def test_http_auth_and_stateless_tool_calls(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    _paths(monkeypatch, tmp_path)
    token = "synthetic-plugin-token-for-testing"
    server = build_control_plugin(token=token)
    app = server.streamable_http_app()
    async with server.session_manager.run():
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app), base_url="http://127.0.0.1:8765",
            headers={"Accept": "application/json, text/event-stream"},
        ) as client:
            request = {"jsonrpc": "2.0", "id": 1, "method": "tools/list"}
            assert (await client.post("/mcp", json=request)).status_code == 401
            assert (await client.post(
                "/mcp", json=request, headers={"Authorization": "Bearer wrong"},
            )).status_code == 401
            client.headers["Authorization"] = f"Bearer {token}"
            result = await client.post("/mcp", json=request)
            assert result.status_code == 200
            assert "mcp-session-id" not in result.headers
            assert "exec_command" in {tool["name"] for tool in result.json()["result"]["tools"]}
            # A separate request needs no sticky HTTP session and performs a real
            # harmless shell write. No POYP account or network calls are used.
            response = await client.post("/mcp", json={
                "jsonrpc": "2.0", "id": 2, "method": "tools/call",
                "params": {"name": "exec_command", "arguments": {
                    "cmd": "printf connected > smoke.txt", "workdir": str(tmp_path),
                }},
            })
            assert response.status_code == 200
            assert not response.json()["result"].get("isError")
            assert (tmp_path / "smoke.txt").read_text() == "connected"


@pytest.mark.anyio
async def test_stdio_plugin_real_roundtrip(tmp_path: Path) -> None:
    # The same subprocess transport tunnel-client can launch. Force a nonexistent
    # token path to prove stdio needs neither an HTTP token nor /data access.
    params = StdioServerParameters(
        command=sys.executable,
        args=["-m", "poyto.control_plugin", "--transport", "stdio"],
        env={
            "POYTO_PLUGIN_ROOTS": str(tmp_path),
            "POYTO_PLUGIN_EXEC_MODE": "container",
            "POYTO_PLUGIN_TOKEN_FILE": str(tmp_path / "unused" / "token"),
            "POYTO_SESSION_FILE": str(tmp_path / "unused" / "session.json"),
        },
    )
    async with stdio_client(params) as (reader, writer):
        async with ClientSession(reader, writer) as session:
            initialized = await session.initialize()
            assert initialized.serverInfo.name == "Poyto Server Control"
            listing = await session.list_tools()
            tools = {tool.name: tool for tool in listing.tools}
            for name in ["apply_patch", "exec_command", "write_stdin", "buy", "sell"]:
                assert tools[name].annotations and tools[name].annotations.readOnlyHint is False
            patched = await session.call_tool("apply_patch", {"patch": (
                "*** Begin Patch\n*** Add File: smoke.txt\n+patched\n*** End Patch"
            )})
            assert not patched.isError
            read = await session.call_tool("read", {"paths": ["smoke.txt"]})
            assert not read.isError
            assert any("patched" in getattr(item, "text", "") for item in read.content)
            executed = await session.call_tool("exec_command", {
                "cmd": "printf shell >> smoke.txt", "yield_time_ms": 1000,
            })
            assert not executed.isError
            assert (tmp_path / "smoke.txt").read_text() == "patched\nshell"
            denied = await session.call_tool("buy", {
                "market_id": "market-id", "position_index": 0, "point_amount": 1,
            })
            assert denied.isError  # confirmation fails before loading credentials
    assert not (tmp_path / "unused").exists()
