from __future__ import annotations

import argparse
import os
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class MCPSettings:
    transport: str = "stdio"
    host: str = "127.0.0.1"
    port: int = 8765
    read_only: bool = False

    @classmethod
    def from_env(cls) -> "MCPSettings":
        read_only = os.getenv("POYTO_MCP_READ_ONLY", "false").strip().lower() in {
            "1",
            "true",
            "yes",
            "on",
        }
        return cls(
            transport=os.getenv("POYTO_MCP_TRANSPORT", "stdio"),
            host=os.getenv("POYTO_MCP_HOST", "127.0.0.1"),
            port=int(os.getenv("POYTO_MCP_PORT", "8765")),
            read_only=read_only,
        )


def build_parser() -> argparse.ArgumentParser:
    defaults = MCPSettings.from_env()
    parser = argparse.ArgumentParser(description="Expose Poyto as an MCP server")
    parser.add_argument(
        "--transport",
        choices=("stdio", "sse", "streamable-http"),
        default=defaults.transport,
    )
    parser.add_argument("--host", default=defaults.host)
    parser.add_argument("--port", type=int, default=defaults.port)
    parser.add_argument(
        "--read-only",
        action=argparse.BooleanOptionalAction,
        default=defaults.read_only,
        help="Expose only read tools. Recommended for remote deployments.",
    )
    return parser
