from __future__ import annotations

import argparse

import pytest

from poyto.mcp.config import MCPSettings, build_parser, settings_from_args
from poyto.mcp.server import require_confirmation


def test_mcp_parser_defaults_to_stdio(monkeypatch: pytest.MonkeyPatch) -> None:
    for name in (
        "POYTO_MCP_TRANSPORT",
        "POYTO_MCP_HOST",
        "POYTO_MCP_PORT",
        "POYTO_MCP_READ_ONLY",
    ):
        monkeypatch.delenv(name, raising=False)
    args = build_parser().parse_args([])
    assert args.transport == "stdio"
    assert args.host == "127.0.0.1"
    assert args.port == 8765
    assert args.read_only is False
    assert args.print_config is False


def test_mcp_settings_read_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("POYTO_MCP_TRANSPORT", "streamable-http")
    monkeypatch.setenv("POYTO_MCP_HOST", "127.0.0.1")
    monkeypatch.setenv("POYTO_MCP_PORT", "9000")
    monkeypatch.setenv("POYTO_MCP_READ_ONLY", "true")
    settings = MCPSettings.from_env()
    assert settings.transport == "streamable-http"
    assert settings.host == "127.0.0.1"
    assert settings.port == 9000
    assert settings.read_only is True


def test_mcp_parser_accepts_streamable_http() -> None:
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


def test_settings_public_dict_contains_no_credentials() -> None:
    settings = MCPSettings(transport="stdio", host="127.0.0.1", port=8765, read_only=True)
    assert settings.as_public_dict() == {
        "transport": "stdio",
        "host": "127.0.0.1",
        "port": 8765,
        "read_only": True,
    }


def test_settings_reject_invalid_port() -> None:
    args = argparse.Namespace(
        transport="streamable-http",
        host="127.0.0.1",
        port=70000,
        read_only=True,
    )
    with pytest.raises(ValueError, match="between 1 and 65535"):
        settings_from_args(args)


def test_mutation_requires_explicit_confirmation() -> None:
    with pytest.raises(ValueError, match="confirm=true"):
        require_confirmation(False, "buy")


def test_mutation_accepts_confirmation() -> None:
    require_confirmation(True, "sell")
