from __future__ import annotations

import argparse
import os
from collections.abc import Mapping
from typing import Any

from .auto import PoytoClient
from .config import env_bool


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


def build_server(
    *,
    host: str = "127.0.0.1",
    port: int = 8765,
    read_only: bool = False,
    server_name: str = "Poyto",
    extra_instructions: str | None = None,
    fastmcp_kwargs: Mapping[str, Any] | None = None,
) -> Any:
    """Build the optional MCP server without making MCP a core dependency."""
    try:
        from mcp.server.fastmcp import FastMCP
        from mcp.types import ToolAnnotations
    except ImportError as exc:  # pragma: no cover - depends on optional extra
        raise RuntimeError(
            "MCP support is not installed. Install Poyto with: pip install -e '.[agent]'"
        ) from exc

    mode_instructions = (
        "This MCP server is running in read-only mode; state-changing tools are intentionally "
        "not exposed."
        if read_only
        else (
            "State-changing tools require confirm=true and must only be used after the user "
            "explicitly confirms the exact operation."
        )
    )
    instructions = (
        "Use Poyto as the authoritative source for the user's current POYP account, "
        "markets, portfolio, activity and balance state. Read operations may be run "
        "directly. When a question depends on current real-world news or likely market "
        "outcomes, use the host client's web/search tools if available and clearly keep "
        "external research separate from POYP-provided data. Do not infer external facts "
        "from market prices alone. Never ask the user to paste access or refresh tokens "
        "into chat; authentication is loaded from Poyto's persisted session/environment. "
        + mode_instructions
    )
    if extra_instructions:
        instructions += " " + extra_instructions.strip()

    mcp = FastMCP(
        server_name,
        instructions=(
            instructions
        ),
        host=host,
        port=port,
        **dict(fastmcp_kwargs or {}),
    )

    read_annotations = ToolAnnotations(
        readOnlyHint=True,
        destructiveHint=False,
        idempotentHint=True,
        openWorldHint=True,
    )

    @mcp.tool(annotations=read_annotations)
    def health() -> Any:
        """Check whether the POYP API is reachable."""
        return _client_call("health")

    @mcp.tool(annotations=read_annotations)
    def profile() -> Any:
        """Get the authenticated account profile."""
        return _client_call("profile")

    @mcp.tool(annotations=read_annotations)
    def balances() -> Any:
        """Get current account balances/points."""
        return _client_call("balances")

    @mcp.tool(annotations=read_annotations)
    def portfolio() -> Any:
        """Get the current portfolio and open positions."""
        return _client_call("portfolio")

    @mcp.tool(annotations=read_annotations)
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

    @mcp.tool(annotations=read_annotations)
    def market(market_id: str) -> Any:
        """Get details for one market by ID."""
        return _client_call("market", market_id)

    @mcp.tool(annotations=read_annotations)
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

    @mcp.tool(annotations=read_annotations)
    def asset_price(asset: str = "BTC") -> Any:
        """Get the observed POYP asset price endpoint (for example BTC)."""
        return _client_call("asset_price", asset)

    @mcp.tool(annotations=read_annotations)
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

    @mcp.tool(annotations=read_annotations)
    def login_bonus() -> Any:
        """Get the current login-streak/login-bonus state."""
        return _client_call("login_bonus")

    @mcp.tool(annotations=read_annotations)
    def unread_notification_count() -> Any:
        """Get the current unread notification count."""
        return _client_call("unread_notification_count")

    @mcp.tool(annotations=read_annotations)
    def home_sections() -> Any:
        """Get POYP's current home discovery sections."""
        return _client_call("home_sections")

    @mcp.tool(annotations=read_annotations)
    def home_tabs() -> Any:
        """Get POYP's current home tab configuration."""
        return _client_call("home_tabs")

    @mcp.tool(annotations=read_annotations)
    def interest_subcategories(category: str = "all") -> Any:
        """Get POYP interest subcategories for a category (defaults to all)."""
        return _client_call("interest_subcategories", category)

    @mcp.tool(annotations=read_annotations)
    def campaign_banners() -> Any:
        """Get the current POYP campaign banners."""
        return _client_call("campaign_banners")

    @mcp.tool(annotations=read_annotations)
    def loss_gacha_status(market_id: str | None = None) -> Any:
        """Check current loss-gacha eligibility, optionally for one resolved market."""
        return _client_call("loss_gacha_status", market_id)

    if not read_only:
        mutation_annotations = ToolAnnotations(
            readOnlyHint=False,
            destructiveHint=True,
            idempotentHint=False,
            openWorldHint=True,
        )
        ticket_annotations = ToolAnnotations(
            readOnlyHint=False,
            destructiveHint=False,
            idempotentHint=False,
            openWorldHint=True,
        )

        @mcp.tool(annotations=ticket_annotations)
        def loss_gacha_ticket(market_id: str, confirm: bool = False) -> Any:
            """Create a short-lived loss-gacha ticket. Requires explicit confirm=true."""
            _require_confirmation(confirm, "loss_gacha_ticket")
            return _client_call("create_loss_gacha_ticket", market_id)

        @mcp.tool(annotations=mutation_annotations)
        def loss_gacha_claim(
            market_id: str,
            ticket_id: str,
            kind: str = "video_gacha",
            confirm: bool = False,
        ) -> Any:
            """Claim an eligible loss-gacha reward after the required reward flow has completed."""
            _require_confirmation(confirm, "loss_gacha_claim")
            return _client_call("claim_loss_gacha", market_id, ticket_id, kind=kind)

        @mcp.tool(annotations=mutation_annotations)
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

        @mcp.tool(annotations=mutation_annotations)
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
    parser.add_argument(
        "--read-only",
        action=argparse.BooleanOptionalAction,
        default=env_bool("POYTO_MCP_READ_ONLY", default=False),
        help="Expose only read tools (recommended for ChatGPT Web and remote deployments).",
    )
    return parser


def main(argv: list[str] | None = None) -> None:
    args = build_parser().parse_args(argv)
    server = build_server(host=args.host, port=args.port, read_only=args.read_only)
    server.run(transport=args.transport)


if __name__ == "__main__":
    main()
