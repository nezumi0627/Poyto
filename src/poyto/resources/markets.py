from __future__ import annotations

from collections.abc import Iterator, Sequence
from typing import Any

from .._resource import ResourceMixin


class MarketsMixin(ResourceMixin):
    def markets(
        self,
        *,
        phase: str = "open",
        limit: int = 100,
        feed: str | None = "home",
        sort: str | None = "recommended",
        cursor: str | None = None,
        **extra: Any,
    ) -> Any:
        params: dict[str, Any] = {"phase": phase, "limit": limit, **extra}
        if feed is not None:
            params["feed"] = feed
        if sort is not None:
            params["sort"] = sort
        if cursor is not None:
            params["cursor"] = cursor
        return self.get("/api/markets", params=params)

    def iter_markets(self, **kwargs: Any) -> Iterator[dict[str, Any]]:
        cursor = kwargs.pop("cursor", None)
        while True:
            data = self.markets(cursor=cursor, **kwargs)
            yield from data.get("items", [])
            cursor = data.get("nextCursor")
            if not cursor:
                return

    def market(self, market_id: str) -> Any:
        return self.get(f"/api/markets/{market_id}")

    def related_markets(self, market_id: str) -> Any:
        return self.get(f"/api/markets/{market_id}/related")

    def market_screen_auxiliary(self, market_id: str, *, tf: str = "max") -> Any:
        return self.get(f"/api/markets/{market_id}/screen-auxiliary", params={"tf": tf})

    def my_market_positions(self, market_id: str) -> Any:
        return self.get(f"/api/me/markets/{market_id}/positions")

    def market_activity(
        self,
        market_id: str,
        *,
        limit: int = 50,
        types: str = "all",
        cursor: str | None = None,
    ) -> Any:
        return self.get(
            f"/api/markets/{market_id}/activity",
            params=self._cursor_params({"limit": limit, "types": types}, cursor),
        )

    def market_charts(self, market_ids: Sequence[str], *, tf: str = "max") -> Any:
        return self.get(
            "/api/markets/charts",
            params={"ids": ",".join(market_ids), "tf": tf},
        )

    def asset_price(self, asset: str = "BTC") -> Any:
        # Observed HAR path is plural: /api/prices/BTC.
        return self.get(f"/api/prices/{asset.upper()}")

    def comment_moderation_status(self) -> Any:
        return self.get("/api/comments/moderation-status")
