from __future__ import annotations

from .mcp.__main__ import main
from .mcp.config import build_parser
from .mcp.server import build_server, require_confirmation

# Backward-compatible alias for callers/tests using the old private helper name.
_require_confirmation = require_confirmation

__all__ = [
    "_require_confirmation",
    "build_parser",
    "build_server",
    "main",
    "require_confirmation",
]


if __name__ == "__main__":
    main()
