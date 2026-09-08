from __future__ import annotations

import os
import uuid
from datetime import datetime, timezone
from typing import Any, Iterator, Mapping, Sequence

import httpx

from .exceptions import APIError, AuthenticationError
from .models import AuthSession, DeviceInfo


class PoytoClient:
    """Synchronous unofficial POYP API client reconstructed from observed app traffic."""

    API_BASE = "https://api.poyp.app"
    AUTH_BASE = "https://auth.poyp.app"
    DEFAULT_SUPABASE_KEY = "sb_publishable_IsB7Xd-wxlyad8v8sMDNmA_n7gj8OF0"

    def __init__(
        self,
        *,
        access_token: str | None = None,
        refresh_token: str | None = None,
        supabase_key: str | None = None,
        device: DeviceInfo | None = None,
        timeout: float = 20.0,
        transport: httpx.BaseTransport | None = None,
        api_base: str | None = None,
        auth_base: str | None = None,
    ) -> None:
        self.api_base = (api_base or self.API_BASE).rstrip("/")
        self.auth_base = (auth_base or self.AUTH_BASE).rstrip("/")
        self.supabase_key = supabase_key or os.getenv("POYP_SUPABASE_KEY") or self.DEFAULT_SUPABASE_KEY
        self.device = device or DeviceInfo.from_env()
        self.session = AuthSession(access_token, refresh_token) if access_token else None
        self.http = httpx.Client(
            timeout=timeout,
            follow_redirects=True,
            transport=transport,
            headers={"accept": "application/json", "x-client-info": "Poyto"},
        )

    @classmethod
    def from_env(cls, **kwargs: Any) -> "PoytoClient":
        return cls(
            access_token=os.getenv("POYP_ACCESS_TOKEN"),
            refresh_token=os.getenv("POYP_REFRESH_TOKEN"),
            **kwargs,
        )

    def __enter__(self) -> "PoytoClient":
        return self

    def __exit__(self, *_: Any) -> None:
        self.close()

    def close(self) -> None:
        self.http.close()

    # Authentication
    def login_with_apple(
        self,
        *,
        id_token: str,
        apple_access_token: str | None = None,
        nonce: str | None = None,
    ) -> AuthSession:
        payload: dict[str, Any] = {"provider": "apple", "id_token": id_token, "gotrue_meta_security": {}}
        if apple_access_token:
            payload["access_token"] = apple_access_token
        if nonce:
            payload["nonce"] = nonce
        response = self.http.post(
            f"{self.auth_base}/auth/v1/token",
            params={"grant_type": "id_token"},
            headers=self._supabase_headers(),
            json=payload,
        )
        self.session = AuthSession.from_json(self._decode(response))
        return self.session

    def refresh(self, refresh_token: str | None = None) -> AuthSession:
        token = refresh_token or (self.session.refresh_token if self.session else None)
        if not token:
            raise AuthenticationError("refresh token is not available")
        response = self.http.post(
            f"{self.auth_base}/auth/v1/token",
            params={"grant_type": "refresh_token"},
            headers=self._supabase_headers(),
            json={"refresh_token": token},
        )
        self.session = AuthSession.from_json(self._decode(response))
        return self.session

    def set_access_token(self, access_token: str, refresh_token: str | None = None) -> None:
        self.session = AuthSession(access_token, refresh_token)

    def logout(self, scope: str = "global") -> None:
        if not self.session:
            return
        response = self.http.post(
            f"{self.auth_base}/auth/v1/logout",
            params={"scope": scope},
            headers={**self._supabase_headers(), **self._auth_header()},
        )
        if response.status_code not in {200, 204}:
            self._decode(response)
        self.session = None

    # Account
    def health(self) -> Any: return self.get("/api/health", auth=False)
    def profile(self) -> Any: return self.get("/api/me/profile")
    def balances(self) -> Any: return self.get("/api/me/balances")
    def portfolio(self) -> Any: return self.get("/api/me/portfolio")
    def balance_history(self, tf: str = "1m") -> Any: return self.get("/api/me/balance-history", params={"tf": tf})
    def expiring_balances(self) -> Any: return self.get("/api/me/expiring-balances")
    def missions(self) -> Any: return self.get("/api/me/missions")
    def login_streak(self) -> Any: return self.get("/api/me/login-streak")
    def campaign_results(self) -> Any: return self.get("/api/me/campaign-results")
    def notifications(self, **params: Any) -> Any: return self.get("/api/me/notifications", params=params or None)
    def unread_notification_count(self) -> Any: return self.get("/api/me/notifications/unread-count")
    def blocked_users(self) -> Any: return self.get("/api/me/blocked-users")
    def walking_challenge_status(self) -> Any: return self.get("/api/walking-challenge/status")

    def portfolio_history(self, *, tab: str = "active", sort: str = "newest", limit: int = 30, cursor: str | None = None) -> Any:
        return self.get("/api/me/portfolio/history", params=self._cursor_params({"tab": tab, "sort": sort, "limit": limit}, cursor))

    def balance_transactions(self, *, currency: str = "point", limit: int = 30, cursor: str | None = None) -> Any:
        return self.get("/api/me/balance-transactions", params=self._cursor_params({"currency": currency, "limit": limit}, cursor))

    def provider_rewards(self, *, source: str = "skyflag", since: str | None = None) -> Any:
        params = {"source": source}
        if since: params["since"] = since
        return self.get("/api/me/provider-rewards", params=params)

    def loss_gacha_status(self, market_id: str | None = None) -> Any:
        return self.get("/api/me/loss-gacha/status", params={"marketId": market_id} if market_id else None)

    def mark_all_notifications_read(self) -> Any: return self.post("/api/me/notifications/read-all")
    def register_push_token(self, token: str, *, platform: str = "ios") -> Any: return self.post("/api/me/push-tokens", json={"token": token, "platform": platform})
    def claim_ad_reward(self, *, source: str = "watch_ad") -> Any: return self.post("/api/me/ad-rewards/claim", params={"source": source})

    # Referral
    def referral_code(self) -> Any: return self.get("/api/me/referral-code")
    def referral_stats(self) -> Any: return self.get("/api/me/referral-stats")
    def referral_code_available(self, code: str) -> Any: return self.get("/api/me/referral-code/availability", params={"code": code})
    def set_referral_code(self, code: str) -> Any: return self.put("/api/me/referral-code", json={"code": code})

    # Markets
    def markets(self, *, phase: str = "open", limit: int = 100, feed: str | None = "home", sort: str | None = "recommended", cursor: str | None = None, **extra: Any) -> Any:
        params: dict[str, Any] = {"phase": phase, "limit": limit, **extra}
        if feed is not None: params["feed"] = feed
        if sort is not None: params["sort"] = sort
        if cursor is not None: params["cursor"] = cursor
        return self.get("/api/markets", params=params)

    def iter_markets(self, **kwargs: Any) -> Iterator[dict[str, Any]]:
        cursor = kwargs.pop("cursor", None)
        while True:
            data = self.markets(cursor=cursor, **kwargs)
            yield from data.get("items", [])
            cursor = data.get("nextCursor")
            if not cursor: return

    def market(self, market_id: str) -> Any: return self.get(f"/api/markets/{market_id}")
    def related_markets(self, market_id: str) -> Any: return self.get(f"/api/markets/{market_id}/related")
    def my_market_positions(self, market_id: str) -> Any: return self.get(f"/api/me/markets/{market_id}/positions")
    def comment_moderation_status(self) -> Any: return self.get("/api/comments/moderation-status")

    def market_screen_auxiliary(self, market_id: str, *, tf: str = "max") -> Any:
        return self.get(f"/api/markets/{market_id}/screen-auxiliary", params={"tf": tf})

    def market_activity(self, market_id: str, *, limit: int = 50, types: str = "all", cursor: str | None = None) -> Any:
        return self.get(f"/api/markets/{market_id}/activity", params=self._cursor_params({"limit": limit, "types": types}, cursor))

    def market_charts(self, market_ids: Sequence[str], *, tf: str = "max") -> Any:
        return self.get("/api/markets/charts", params={"ids": ",".join(market_ids), "tf": tf})

    def asset_price(self, asset: str = "BTC") -> Any: return self.get(f"/api/price/{asset.upper()}")

    # Trades
    def buy(self, *, market_id: str, position_index: int, point_amount: float, order_surface: str = "home_card", display_preset: str = "dominance", entry_point: str = "home_feed", request_id: str | None = None, session_id: str | None = None, device_id: str | None = None) -> Any:
        return self.post("/api/trades/buy", json={
            "marketId": market_id, "positionIndex": position_index, "pointAmount": point_amount,
            "orderSurface": order_surface, "displayPreset": display_preset, "entryPoint": entry_point,
            "requestId": request_id or str(uuid.uuid4()), "sessionId": session_id or str(uuid.uuid4()),
            "deviceId": device_id or self.device.device_id or str(uuid.uuid4()),
        })

    def sell(self, *, market_id: str, position_index: int, shares: float, order_surface: str = "modal_position_sell", entry_point: str = "mypage", session_id: str | None = None, device_id: str | None = None) -> Any:
        return self.post("/api/trades/sell", json={
            "marketId": market_id, "positionIndex": position_index, "shares": shares,
            "orderSurface": order_surface, "entryPoint": entry_point,
            "sessionId": session_id or str(uuid.uuid4()), "deviceId": device_id or self.device.device_id or str(uuid.uuid4()),
        })

    # Comments
    def post_comment(self, market_id: str, body: str, *, parent_comment_id: str | None = None) -> Any:
        payload: dict[str, Any] = {"body": body}
        if parent_comment_id: payload["parentCommentId"] = parent_comment_id
        return self.post(f"/api/markets/{market_id}/comments", json=payload)
    def edit_comment(self, comment_id: str, body: str) -> Any: return self.put(f"/api/comments/{comment_id}", json={"body": body})
    def delete_comment(self, comment_id: str) -> Any: return self.delete(f"/api/comments/{comment_id}")
    def like_comment(self, comment_id: str) -> Any: return self.post(f"/api/comments/{comment_id}/likes")

    # Discovery / social
    def home_sections(self) -> Any: return self.get("/api/home-sections")
    def home_tabs(self) -> Any: return self.get("/api/home-tabs")
    def search_sections(self, **params: Any) -> Any: return self.get("/api/search/sections", params=params or None)
    def interest_subcategories(self, category: str = "all") -> Any: return self.get(f"/api/interests/{category}/subcategories")
    def campaign_banners(self) -> Any: return self.get("/api/campaign-banners")
    def onboarding(self) -> Any: return self.get("/api/onboarding")
    def global_chat(self, *, limit: int = 20, **extra: Any) -> Any: return self.get("/api/global-chat/messages", params={"limit": limit, **extra})
    def recent_trades(self, *, limit: int = 20, offset: int = 0) -> Any: return self.get("/api/leaderboard/recent-trades", params={"limit": limit, "offset": offset})
    def recent_comments(self, *, limit: int = 20, offset: int = 0) -> Any: return self.get("/api/leaderboard/recent-comments", params={"limit": limit, "offset": offset})
    def followed_trades(self, *, limit: int = 20, offset: int = 0) -> Any: return self.get("/api/timeline/followed-trades", params={"limit": limit, "offset": offset})

    def leaderboard_traders(self, *, period: str = "weekly", limit: int = 20, offset: int = 0) -> Any:
        return self.get("/api/leaderboard/traders", params={"period": period, "limit": limit, "offset": offset})
    def rising_markets(self, *, period: str = "24h", limit: int = 20, offset: int = 0) -> Any:
        return self.get("/api/leaderboard/rising-markets", params={"period": period, "limit": limit, "offset": offset})

    def user_profile(self, user_id: str) -> Any: return self.get(f"/api/users/{user_id}")
    def user_follow_status(self, user_id: str) -> Any: return self.get(f"/api/users/{user_id}/follow-status")
    def user_team_follows(self, user_id: str) -> Any: return self.get(f"/api/users/{user_id}/team-follows")
    def user_balance_history(self, user_id: str, *, tf: str = "1m") -> Any: return self.get(f"/api/users/{user_id}/balance-history", params={"tf": tf})
    def follow_user(self, user_id: str) -> Any: return self.post(f"/api/users/{user_id}/follow")
    def unfollow_user(self, user_id: str) -> Any: return self.delete(f"/api/users/{user_id}/follow")

    def user_followers(self, user_id: str, *, limit: int = 30, cursor: str | None = None) -> Any:
        return self.get(f"/api/users/{user_id}/followers", params=self._cursor_params({"limit": limit}, cursor))
    def user_following(self, user_id: str, *, limit: int = 30, cursor: str | None = None) -> Any:
        return self.get(f"/api/users/{user_id}/following", params=self._cursor_params({"limit": limit}, cursor))
    def user_portfolio_history(self, user_id: str, *, tab: str = "active", sort: str = "newest", limit: int = 30, cursor: str | None = None) -> Any:
        return self.get(f"/api/users/{user_id}/portfolio/history", params=self._cursor_params({"tab": tab, "sort": sort, "limit": limit}, cursor))

    # Events
    def send_events(self, events: Sequence[Mapping[str, Any]]) -> Any: return self.post("/api/events", json={"events": list(events)})
    def make_event(self, event_name: str, payload: Mapping[str, Any], *, event_version: int = 1, event_id: str | None = None, session_id: str | None = None, device_id: str | None = None) -> dict[str, Any]:
        return {
            "event_id": event_id or str(uuid.uuid4()), "event_name": event_name, "event_version": event_version,
            "occurred_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            "session_id": session_id or str(uuid.uuid4()), "device_id": device_id or self.device.device_id or str(uuid.uuid4()),
            "app_version": self.device.app_version, "platform": self.device.os, "payload": dict(payload),
        }

    # Generic HTTP
    def request(self, method: str, path: str, *, params: Mapping[str, Any] | None = None, json: Any = None, auth: bool = True, headers: Mapping[str, str] | None = None) -> Any:
        path = path if path.startswith("/") else f"/{path}"
        request_headers = self._poyp_headers(auth=auth)
        if headers: request_headers.update(headers)
        response = self.http.request(method.upper(), f"{self.api_base}{path}", params=dict(params) if params else None, json=json, headers=request_headers)
        return self._decode(response)

    def get(self, path: str, *, params: Mapping[str, Any] | None = None, auth: bool = True) -> Any: return self.request("GET", path, params=params, auth=auth)
    def post(self, path: str, *, params: Mapping[str, Any] | None = None, json: Any = None, auth: bool = True) -> Any: return self.request("POST", path, params=params, json=json, auth=auth)
    def put(self, path: str, *, params: Mapping[str, Any] | None = None, json: Any = None, auth: bool = True) -> Any: return self.request("PUT", path, params=params, json=json, auth=auth)
    def patch(self, path: str, *, params: Mapping[str, Any] | None = None, json: Any = None, auth: bool = True) -> Any: return self.request("PATCH", path, params=params, json=json, auth=auth)
    def delete(self, path: str, *, params: Mapping[str, Any] | None = None, json: Any = None, auth: bool = True) -> Any: return self.request("DELETE", path, params=params, json=json, auth=auth)

    @staticmethod
    def _cursor_params(params: dict[str, Any], cursor: str | None) -> dict[str, Any]:
        if cursor is not None: params["cursor"] = cursor
        return params

    def _auth_header(self) -> dict[str, str]:
        if not self.session: raise AuthenticationError("client is not authenticated")
        return {"authorization": f"Bearer {self.session.access_token}"}

    def _supabase_headers(self) -> dict[str, str]:
        return {"apikey": self.supabase_key, "authorization": f"Bearer {self.supabase_key}"}

    def _poyp_headers(self, *, auth: bool) -> dict[str, str]:
        headers = {
            "accept": "application/json", "x-poyp-app-version": self.device.app_version,
            "x-poyp-os": self.device.os, "x-poyp-is-device": "true" if self.device.is_device else "false",
        }
        optional = {
            "x-poyp-os-version": self.device.os_version, "x-poyp-device-model": self.device.device_model,
            "x-poyp-device-id": self.device.device_id, "x-poyp-vendor-id": self.device.vendor_id,
            "x-poyp-ota-generation": self.device.ota_generation,
        }
        headers.update({k: v for k, v in optional.items() if v is not None})
        if auth: headers.update(self._auth_header())
        return headers

    @staticmethod
    def _decode(response: httpx.Response) -> Any:
        if response.is_success:
            if not response.content: return None
            try: return response.json()
            except ValueError: return response.text
        try: body: Any = response.json()
        except ValueError: body = response.text[:2000]
        raise APIError(
            f"POYP API returned HTTP {response.status_code}", status_code=response.status_code,
            method=response.request.method, url=str(response.request.url), response_body=body,
        )
