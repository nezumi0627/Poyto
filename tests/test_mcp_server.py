from __future__ import annotations

import pytest

from poyto.mcp_server import _require_confirmation, build_parser, build_server


def test_mcp_parser_defaults_to_stdio() -> None:
    args = build_parser().parse_args([])
    assert args.transport == "stdio"
    assert args.host == "127.0.0.1"
    assert args.port == 8765
    assert args.read_only is False


def test_mcp_parser_accepts_streamable_http_and_read_only() -> None:
    args = build_parser().parse_args(
        [
            "--transport",
            "streamable-http",
            "--host",
            "0.0.0.0",
            "--port",
            "9000",
            "--read-only",
        ]
    )
    assert args.transport == "streamable-http"
    assert args.host == "0.0.0.0"
    assert args.port == 9000
    assert args.read_only is True


def test_mcp_parser_reads_read_only_from_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("POYTO_MCP_READ_ONLY", "true")
    assert build_parser().parse_args([]).read_only is True


def test_mutation_requires_explicit_confirmation() -> None:
    with pytest.raises(ValueError, match="confirm=true"):
        _require_confirmation(False, "buy")


def test_mutation_accepts_confirmation() -> None:
    _require_confirmation(True, "sell")


@pytest.mark.anyio
async def test_read_only_server_exposes_only_read_tools() -> None:
    server = build_server(read_only=True)
    tools = await server.list_tools()
    names = {tool.name for tool in tools}
    assert {"health", "profile", "balances", "portfolio", "markets", "market"} <= names
    assert {"buy", "sell", "loss_gacha_ticket", "loss_gacha_claim"}.isdisjoint(names)
    assert all(tool.annotations and tool.annotations.readOnlyHint for tool in tools)


@pytest.mark.anyio
async def test_full_server_marks_mutations_as_writes() -> None:
    server = build_server(read_only=False)
    tools = {tool.name: tool for tool in await server.list_tools()}
    assert tools["markets"].annotations and tools["markets"].annotations.readOnlyHint is True
    assert tools["buy"].annotations and tools["buy"].annotations.readOnlyHint is False
    assert tools["buy"].annotations.destructiveHint is True
