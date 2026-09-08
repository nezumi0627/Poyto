from __future__ import annotations

from typing import Any

from .._resource import ResourceMixin


class SocialMixin(ResourceMixin):
    def post_comment(
        self,
        market_id: str,
        body: str,
        *,
        parent_comment_id: str | None = None,
    ) -> Any:
        payload: dict[str, Any] = {"body": body}
        if parent_comment_id:
            payload["parentCommentId"] = parent_comment_id
        return self.post(f"/api/markets/{market_id}/comments", json=payload)

    def edit_comment(self, comment_id: str, body: str) -> Any:
        return self.put(f"/api/comments/{comment_id}", json={"body": body})

    def delete_comment(self, comment_id: str) -> Any:
        return self.delete(f"/api/comments/{comment_id}")

    def like_comment(self, comment_id: str) -> Any:
        return self.post(f"/api/comments/{comment_id}/likes")

    def global_chat(self, *, limit: int = 20, **extra: Any) -> Any:
        return self.get("/api/global-chat/messages", params={"limit": limit, **extra})

    def leaderboard_traders(
        self,
        *,
        period: str = "weekly",
        limit: int = 20,
        offset: int = 0,
    ) -> Any:
        return self.get(
            "/api/leaderboard/traders",
            params={"period": period, "limit": limit, "offset": offset},
        )

    def recent_trades(self, *, limit: int = 20, offset: int = 0) -> Any:
        return self.get(
            "/api/leaderboard/recent-trades",
            params={"limit": limit, "offset": offset},
        )

    def recent_comments(self, *, limit: int = 20, offset: int = 0) -> Any:
        return self.get(
            "/api/leaderboard/recent-comments",
            params={"limit": limit, "offset": offset},
        )

    def rising_markets(
        self,
        *,
        period: str = "24h",
        limit: int = 20,
        offset: int = 0,
    ) -> Any:
        return self.get(
            "/api/leaderboard/rising-markets",
            params={"period": period, "limit": limit, "offset": offset},
        )

    def followed_trades(self, *, limit: int = 20, offset: int = 0) -> Any:
        return self.get(
            "/api/timeline/followed-trades",
            params={"limit": limit, "offset": offset},
        )

    def user_profile(self, user_id: str) -> Any:
        return self.get(f"/api/users/{user_id}")

    def user_follow_status(self, user_id: str) -> Any:
        return self.get(f"/api/users/{user_id}/follow-status")

    def user_team_follows(self, user_id: str) -> Any:
        return self.get(f"/api/users/{user_id}/team-follows")

    def user_followers(
        self,
        user_id: str,
        *,
        limit: int = 30,
        cursor: str | None = None,
    ) -> Any:
        return self.get(
            f"/api/users/{user_id}/followers",
            params=self._cursor_params({"limit": limit}, cursor),
        )

    def user_following(
        self,
        user_id: str,
        *,
        limit: int = 30,
        cursor: str | None = None,
    ) -> Any:
        return self.get(
            f"/api/users/{user_id}/following",
            params=self._cursor_params({"limit": limit}, cursor),
        )

    def user_balance_history(self, user_id: str, *, tf: str = "1m") -> Any:
        return self.get(f"/api/users/{user_id}/balance-history", params={"tf": tf})

    def user_portfolio_history(
        self,
        user_id: str,
        *,
        tab: str = "active",
        sort: str = "newest",
        limit: int = 30,
        cursor: str | None = None,
    ) -> Any:
        return self.get(
            f"/api/users/{user_id}/portfolio/history",
            params=self._cursor_params({"tab": tab, "sort": sort, "limit": limit}, cursor),
        )

    def follow_user(self, user_id: str) -> Any:
        return self.post(f"/api/users/{user_id}/follow")

    def unfollow_user(self, user_id: str) -> Any:
        return self.delete(f"/api/users/{user_id}/follow")
