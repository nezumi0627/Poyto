from __future__ import annotations

import uuid
from typing import Any

from .._resource import ResourceMixin


class TradesMixin(ResourceMixin):
    def buy(
        self,
        *,
        market_id: str,
        position_index: int,
        point_amount: float,
        order_surface: str = "home_card",
        display_preset: str = "dominance",
        entry_point: str = "home_feed",
        request_id: str | None = None,
        session_id: str | None = None,
        device_id: str | None = None,
    ) -> Any:
        return self.post(
            "/api/trades/buy",
            json={
                "marketId": market_id,
                "positionIndex": position_index,
                "pointAmount": point_amount,
                "orderSurface": order_surface,
                "requestId": request_id or str(uuid.uuid4()),
                "displayPreset": display_preset,
                "entryPoint": entry_point,
                "sessionId": session_id or str(uuid.uuid4()),
                "deviceId": device_id or self.device.device_id or str(uuid.uuid4()),
            },
        )

    def sell(
        self,
        *,
        market_id: str,
        position_index: int,
        shares: float,
        order_surface: str = "modal_position_sell",
        entry_point: str = "mypage",
        session_id: str | None = None,
        device_id: str | None = None,
    ) -> Any:
        return self.post(
            "/api/trades/sell",
            json={
                "marketId": market_id,
                "positionIndex": position_index,
                "shares": shares,
                "orderSurface": order_surface,
                "entryPoint": entry_point,
                "sessionId": session_id or str(uuid.uuid4()),
                "deviceId": device_id or self.device.device_id or str(uuid.uuid4()),
            },
        )
