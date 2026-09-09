from __future__ import annotations

import httpx

from poyto import PoytoClient


def test_login_bonus_matches_observed_status_shape():
    seen: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(request)
        return httpx.Response(
            200,
            json={
                "currentStreakDay": 8,
                "todayReward": 1,
                "claimedToday": True,
                "bonusClaimedToday": False,
                "bonusReward": 1,
                "cycle": [1, 2, 2, 6, 3, 3, 8],
            },
        )

    client = PoytoClient(
        access_token="token",
        auto_load_session=False,
        save_session=False,
        transport=httpx.MockTransport(handler),
    )
    with client:
        result = client.login_bonus()

    assert seen[0].method == "GET"
    assert seen[0].url.path == "/api/me/login-streak"
    assert result["currentStreakDay"] == 8
    assert result["todayReward"] == 1
    assert result["claimedToday"] is True
    assert result["bonusClaimedToday"] is False
    assert result["bonusReward"] == 1
    assert result["cycle"] == [1, 2, 2, 6, 3, 3, 8]
