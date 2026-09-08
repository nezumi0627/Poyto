from __future__ import annotations

import pytest

from poyto.mcp_server import _require_confirmation, build_parser


def test_mcp_parser_defaults_to_stdio() -> None:
    args = build_parser().parse_args([])
    assert args.transport == "stdio"
    assert args.host == "127.0.0.1"
    assert args.port == 8765


def test_mcp_parser_accepts_streamable_http() -> None:
    args = build_parser().parse_args(
        ["--transport", "streamable-http", "--host", "0.0.0.0", "--port", "9000"]
    )
    assert args.transport == "streamable-http"
    assert args.host == "0.0.0.0"
    assert args.port == 9000


def test_mutation_requires_explicit_confirmation() -> None:
    with pytest.raises(ValueError, match="confirm=true"):
        _require_confirmation(False, "buy")


def test_mutation_accepts_confirmation() -> None:
    _require_confirmation(True, "sell")
