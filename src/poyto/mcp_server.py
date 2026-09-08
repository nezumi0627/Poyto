from __future__ import annotations

import argparse
import os
from typing import Any

from .auto import PoytoClient


def _client_call(method: str, /, *args: Any, **kwargs: Any) -> Any:
    """Run one Poyto client call using the normal persisted-session policy."""
    with PoytoClient() as client:
        return getattr(client, method)(*args, **kwargs)


def _require_confirmation(confirm: bool, action: str) -> None:
    if not confirm:
        raise ValueError(
            f"{action} changes account state. Re-run with confirm=true only after the user "
            "has explicitly confirmed the exact operation."
        )


def build_server(*, host: str = "127.0.0.1", port: int = 8765) -> Any:
    """Build the optional MCP server without making MCP a core dependency."""
    try:
        from mcp.server.fastmcp import FastMCP
    except ImportError as exc:  # pragma: no cover - depends on optional extra
        raise RuntimeError(
            "MCP support is not installed. Install Poyto with: pip install -e '.[agent]'"
        ) from exc

    mcp = FastMCP(
        "Poyto",
        instructions=(
            "Use Poyto to inspect a POYP account and markets. Read operations may be run "
            "directly. Buy/sell tools require confirm=true and must only be used after the "
            "user explicitly confirms the exact market, side/position and amount. Never ask "
            "the user to paste access or refresh tokens into chat; authentication is loaded "
            "from Poyto's local session/environment configuration."
        ),
        host=host,
        port=port,
    )

    @mcp.tool()
    def health() -> Any:
        """Check whether the POYP API is reachable."""
        return _client_call("health")

    @mcp.tool()
    def profile() -> Any:
        """Get the authenticated account profile."""
        return _client_call("profile")

    @mcp.tool()
    def balances() -> Any:
        """Get current account balances/points."""
        return _client_call("balances")

    @mcp.tool()
    def portfolio() -> Any:
        """Get the current portfolio and open positions."""
        return _client_call("portfolio")

    @mcp.tool()
    def markets(
        limit: int = 20,
        phase: str = "open",
        feed: str = "home",
        sort: str = "recommended",
    ) -> Any:
        """List POYP markets. limit is clamped to 1..100."""
        return _client_call(
            "markets",
            limit=max(1, min(limit, 100)),
            phase=phase,
            feed=feed,
            sort=sort,
        )

    @mcp.tool()
    def market(market_id: str) -> Any:
        """Get details for one market by ID."""
        return _client_call("market", market_id)

    @mcp.tool()
    def market_activity(
        market_id: str,
        limit: int = 50,
        types: str = "all",
    ) -> Any:
        """Get recent activity for a market."""
        return _client_call(
            "market_activity",
            market_id,
            limit=max(1, min(limit, 100)),
            types=types,
        )

    @mcp.tool()
    def asset_price(asset: str = "BTC") -> Any:
        """Get the observed POYP asset price endpoint (for example BTC)."""
        return _client_call("asset_price", asset)

    @mcp.tool()
    def transactions(
        currency: str = "point",
        limit: int = 30,
        cursor: str | None = None,
    ) -> Any:
        """Get account balance transactions."""
        return _client_call(
            "balance_transactions",
            currency=currency,
            limit=max(1, min(limit, 100)),
            cursor=cursor,
        )

    @mcp.tool()
    def buy(
        market_id: str,
        position_index: int,
        point_amount: float,
        confirm: bool = False,
    ) -> Any:
        """Buy a market position. Requires explicit confirm=true."""
        _require_confirmation(confirm, "buy")
        if point_amount <= 0:
            raise ValueError("point_amount must be greater than zero")
        if position_index < 0:
            raise ValueError("position_index must be zero or greater")
        return _client_call(
            "buy",
            market_id=market_id,
            position_index=position_index,
            point_amount=point_amount,
        )

    @mcp.tool()
    def sell(
        market_id: str,
        position_index: int,
        shares: float,
        confirm: bool = False,
    ) -> Any:
        """Sell shares from a market position. Requires explicit confirm=true."""
        _require_confirmation(confirm, "sell")
        if shares <= 0:
            raise ValueError("shares must be greater than zero")
        if position_index < 0:
            raise ValueError("position_index must be zero or greater")
        return _client_call(
            "sell",
            market_id=market_id,
            position_index=position_index,
            shares=shares,
        )

    return mcp


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Expose Poyto as an MCP server")
    parser.add_argument(
        "--transport",
        choices=("stdio", "sse", "streamable-http"),
        default=os.getenv("POYTO_MCP_TRANSPORT", "stdio"),
    )
    parser.add_argument("--host", default=os.getenv("POYTO_MCP_HOST", "127.0.0.1"))
    parser.add_argument(
        "--port",
        type=int,
        default=int(os.getenv("POYTO_MCP_PORT", "8765")),
    )
    return parser


def main(argv: list[str] | None = None) -> None:
    args = build_parser().parse_args(argv)
    server = build_server(host=args.host, port=args.port)
    server.run(transport=args.transport)


if __name__ == "__main__":
    main()
