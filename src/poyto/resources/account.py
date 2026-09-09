from __future__ import annotations

from typing import Any, cast

from .._resource import ResourceMixin
from ..models import (
    AdRewardClaimResponse,
    LoginBonusStatus,
    LossGachaClaimResponse,
    LossGachaStatus,
    LossGachaTicketResponse,
)


class AccountMixin(ResourceMixin):
    def health(self) -> Any:
        return self.get("/api/health", auth=False)

    def profile(self) -> Any:
        return self.get("/api/me/profile")

    def balances(self) -> Any:
        return self.get("/api/me/balances")

    def portfolio(self) -> Any:
        return self.get("/api/me/portfolio")

    def portfolio_history(
        self,
        *,
        tab: str = "active",
        sort: str = "newest",
        limit: int = 30,
        cursor: str | None = None,
    ) -> Any:
        return self.get(
            "/api/me/portfolio/history",
            params=self._cursor_params({"tab": tab, "sort": sort, "limit": limit}, cursor),
        )

    def balance_history(self, tf: str = "1m") -> Any:
        return self.get("/api/me/balance-history", params={"tf": tf})

    def balance_transactions(
        self,
        *,
        currency: str = "point",
        limit: int = 30,
        cursor: str | None = None,
    ) -> Any:
        return self.get(
            "/api/me/balance-transactions",
            params=self._cursor_params({"currency": currency, "limit": limit}, cursor),
        )

    def expiring_balances(self) -> Any:
        return self.get("/api/me/expiring-balances")

    def missions(self) -> Any:
        return self.get("/api/me/missions")

    def login_streak(self) -> LoginBonusStatus:
        return cast(LoginBonusStatus, self.get("/api/me/login-streak"))

    def login_bonus(self) -> LoginBonusStatus:
        """Return today's login-bonus/streak state."""
        return self.login_streak()

    def campaign_results(self) -> Any:
        return self.get("/api/me/campaign-results")

    def provider_rewards(self, *, source: str = "skyflag", since: str | None = None) -> Any:
        params: dict[str, Any] = {"source": source}
        if since:
            params["since"] = since
        return self.get("/api/me/provider-rewards", params=params)

    def loss_gacha_status(self, market_id: str | None = None) -> LossGachaStatus:
        params = {"marketId": market_id} if market_id else None
        return cast(LossGachaStatus, self.get("/api/me/loss-gacha/status", params=params))

    def create_loss_gacha_ticket(self, market_id: str) -> LossGachaTicketResponse:
        return cast(
            LossGachaTicketResponse,
            self.post("/api/me/loss-gacha/ticket", json={"marketId": market_id}),
        )

    def claim_loss_gacha(
        self,
        market_id: str,
        ticket_id: str,
        *,
        kind: str = "video_gacha",
    ) -> LossGachaClaimResponse:
        return cast(
            LossGachaClaimResponse,
            self.post(
                "/api/me/loss-gacha/claim",
                json={"marketId": market_id, "kind": kind, "ticketId": ticket_id},
            ),
        )

    def notifications(self, **params: Any) -> Any:
        return self.get("/api/me/notifications", params=params or None)

    def unread_notification_count(self) -> Any:
        return self.get("/api/me/notifications/unread-count")

    def mark_all_notifications_read(self) -> Any:
        return self.post("/api/me/notifications/read-all")

    def register_push_token(self, token: str, *, platform: str = "ios") -> Any:
        return self.post("/api/me/push-tokens", json={"token": token, "platform": platform})

    def claim_ad_reward(self, *, source: str = "watch_ad") -> AdRewardClaimResponse:
        return cast(
            AdRewardClaimResponse,
            self.post("/api/me/ad-rewards/claim", params={"source": source}),
        )

    def blocked_users(self) -> Any:
        return self.get("/api/me/blocked-users")

    def walking_challenge_status(self) -> Any:
        return self.get("/api/walking-challenge/status")

    def referral_code(self) -> Any:
        return self.get("/api/me/referral-code")

    def referral_stats(self) -> Any:
        return self.get("/api/me/referral-stats")

    def referral_code_available(self, code: str) -> Any:
        return self.get("/api/me/referral-code/availability", params={"code": code})

    def set_referral_code(self, code: str) -> Any:
        return self.put("/api/me/referral-code", json={"code": code})
