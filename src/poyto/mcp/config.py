from __future__ import annotations

import argparse
import os
from dataclasses import asdict, dataclass
from typing import Any

_TRUE_VALUES = {"1", "true", "yes", "on"}


def _env_bool(name: str, default: bool = False) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in _TRUE_VALUES


@dataclass(frozen=True, slots=True)
class MCPSettings:
    transport: str = "stdio"
    host: str = "127.0.0.1"
    port: int = 8765
    read_only: bool = False

    @classmethod
    def from_env(cls) -> MCPSettings:
        return cls(
            transport=os.getenv("POYTO_MCP_TRANSPORT", "stdio"),
            host=os.getenv("POYTO_MCP_HOST", "127.0.0.1"),
            port=int(os.getenv("POYTO_MCP_PORT", "8765")),
            read_only=_env_bool("POYTO_MCP_READ_ONLY"),
        )

    def as_public_dict(self) -> dict[str, Any]:
        """Return non-secret MCP runtime settings for diagnostics."""
        return asdict(self)


def settings_from_args(args: argparse.Namespace) -> MCPSettings:
    settings = MCPSettings(
        transport=args.transport,
        host=args.host,
        port=args.port,
        read_only=args.read_only,
    )
    if not 1 <= settings.port <= 65535:
        raise ValueError("MCP port must be between 1 and 65535")
    return settings


def build_parser() -> argparse.ArgumentParser:
    defaults = MCPSettings.from_env()
    parser = argparse.ArgumentParser(
        description="Expose Poyto as an MCP server",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--transport",
        choices=("stdio", "sse", "streamable-http"),
        default=defaults.transport,
        help="MCP transport. stdio is the easiest local integration.",
    )
    parser.add_argument("--host", default=defaults.host, help="HTTP/SSE bind host")
    parser.add_argument("--port", type=int, default=defaults.port, help="HTTP/SSE bind port")
    parser.add_argument(
        "--read-only",
        action=argparse.BooleanOptionalAction,
        default=defaults.read_only,
        help="Expose only read tools. Recommended for remote deployments.",
    )
    parser.add_argument(
        "--print-config",
        action="store_true",
        help="Print the effective non-secret MCP configuration and exit.",
    )
    return parser
