from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from ..auto import PoytoClient


def _client_call(method: str, /, *args: Any, **kwargs: Any) -> Any:
    """Run one Poyto call using the normal persisted-session policy."""
    with PoytoClient() as client:
        return getattr(client, method)(*args, **kwargs)


def require_confirmation(confirm: bool, action: str) -> None:
    """Require an explicit second-stage confirmation for account mutations."""
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
    """Build Poyto's optional MCP server.

    MCP remains an optional dependency so importing the normal Python client does not
    pull the MCP runtime into applications that do not use it.
    """
    try:
        from mcp.server.fastmcp import FastMCP
        from mcp.types import ToolAnnotations
    except ImportError as exc:  # pragma: no cover - optional dependency
        raise RuntimeError(
            "MCP support is not installed. Install Poyto with: pip install 'poyto[agent]'"
        ) from exc

    mode = (
        "This server is read-only; account-changing tools are intentionally not exposed."
        if read_only
        else (
            "Account-changing tools require confirm=true and may only be used after the "
            "user explicitly confirms the exact operation."
        )
    )
    instructions = (
        "Use Poyto as the authoritative source for POYP account state, balances, markets, "
        "portfolio and POYP activity. For current real-world evidence, use the host model's "
        "web/search capability when available and keep external research separate from POYP "
        "data. Never ask the user to paste access or refresh tokens into chat; credentials are "
        "loaded from Poyto's normal local session/environment configuration. "
        + mode
    )
    if extra_instructions:
        instructions += " " + extra_instructions.strip()

    mcp = FastMCP(
        server_name,
        instructions=instructions,
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
        """Get details for one POYP market."""
        return _client_call("market", market_id)

    @mcp.tool(annotations=read_annotations)
    def market_activity(market_id: str, limit: int = 50, types: str = "all") -> Any:
        """Get recent POYP activity for one market."""
        return _client_call(
            "market_activity",
            market_id,
            limit=max(1, min(limit, 100)),
            types=types,
        )

    @mcp.tool(annotations=read_annotations)
    def asset_price(asset: str = "BTC") -> Any:
        """Get the observed POYP asset-price endpoint."""
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
        """Get the current login bonus/streak state."""
        return _client_call("login_bonus")

    @mcp.tool(annotations=read_annotations)
    def unread_notification_count() -> Any:
        """Get the current unread notification count."""
        return _client_call("unread_notification_count")

    @mcp.tool(annotations=read_annotations)
    def loss_gacha_status(market_id: str | None = None) -> Any:
        """Check current loss-gacha eligibility, optionally for one market."""
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
            """Create a short-lived loss-gacha ticket. Requires confirm=true."""
            require_confirmation(confirm, "loss_gacha_ticket")
            return _client_call("create_loss_gacha_ticket", market_id)

        @mcp.tool(annotations=mutation_annotations)
        def loss_gacha_claim(
            market_id: str,
            ticket_id: str,
            kind: str = "video_gacha",
            confirm: bool = False,
        ) -> Any:
            """Claim an eligible loss-gacha reward. Requires confirm=true."""
            require_confirmation(confirm, "loss_gacha_claim")
            return _client_call("claim_loss_gacha", market_id, ticket_id, kind=kind)

        @mcp.tool(annotations=mutation_annotations)
        def buy(
            market_id: str,
            position_index: int,
            point_amount: float,
            confirm: bool = False,
        ) -> Any:
            """Buy a market position. Requires confirm=true."""
            require_confirmation(confirm, "buy")
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
            """Sell shares from a market position. Requires confirm=true."""
            require_confirmation(confirm, "sell")
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
