from __future__ import annotations

import os
from pathlib import Path

import pytest

from poyto.control_exec import ExecManager
from poyto.control_fs import ControlPatcher, ControlReader
from poyto.control_paths import ControlPathError, ControlPaths
from poyto.control_plugin import build_control_plugin, ensure_plugin_token


def _paths(monkeypatch: pytest.MonkeyPatch, root: Path) -> ControlPaths:
    monkeypatch.setenv("POYTO_PLUGIN_ROOTS", str(root))
    monkeypatch.setenv("POYTO_PLUGIN_EXEC_MODE", "container")
    return ControlPaths.from_env()


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
    immediate = manager.exec_command(cmd="printf hello", workdir=str(tmp_path), yield_time_ms=1000)
    assert immediate["exit_code"] == 0
    assert immediate["output"] == "hello"

    background = manager.exec_command(
        cmd="sleep 0.15; printf done",
        workdir=str(tmp_path),
        yield_time_ms=10,
    )
    assert "session_id" in background
    final = manager.write_stdin(session_id=background["session_id"], yield_time_ms=1000)
    assert final["exit_code"] == 0
    assert "done" in final["output"]


def test_exec_batch_keeps_first_nonzero_exit_and_continues(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    manager = ExecManager(_paths(monkeypatch, tmp_path))
    result = manager.exec_command(
        cmds=["export POYTO_TEST_VALUE=works", "false", "printf \"$POYTO_TEST_VALUE\""],
        workdir=str(tmp_path),
        yield_time_ms=1000,
    )
    assert result["exit_code"] == 1
    assert "works" in result["output"]
    assert "command 3/3" in result["output"]


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
