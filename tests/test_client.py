from __future__ import annotations

import json

import httpx
import pytest

from poyto import APIError, AuthenticationError, DeviceInfo, PoytoClient


@pytest.fixture
def recorder():
    seen: list[tuple[str, str, object, dict[str, str]]] = []

    def handler(request: httpx.Request) -> httpx.Response:
        body = json.loads(request.content.decode()) if request.content else None
        seen.append((request.method, str(request.url), body, dict(request.headers)))
        if "/auth/v1/token" in str(request.url):
            return httpx.Response(
                200,
                json={"access_token": "a" * 40, "refresh_token": "r" * 20, "expires_in": 3600},
            )
        if "/api/me/ad-rewards/claim" in str(request.url):
            return httpx.Response(
                200,
                json={
                    "earnId": "00000000-0000-0000-0000-000000000000",
                    "rewardPoints": 5,
                    "pointBalanceAfter": 8,
                    "dailyViewCount": 2,
                    "dailyViewLimit": 5,
                },
            )
        return httpx.Response(200, json={"ok": True})

    return seen, httpx.MockTransport(handler)


def isolated_client(**kwargs):
    return PoytoClient(auto_load_session=False, save_session=False, **kwargs)


def test_observed_request_shapes(recorder):
    seen, transport = recorder
    device = DeviceInfo(
        app_version="1.3.9", os="ios", os_version="26.1", device_model="iPhone",
        device_id="dev", vendor_id="vendor", ota_generation="1030904",
    )
    with isolated_client(access_token="testtoken", device=device, transport=transport) as client:
        client.profile()
        client.markets(limit=20, sort="ending_soon")
        client.market_screen_auxiliary("mid")
        client.buy(market_id="mid", position_index=1, point_amount=10, request_id="rid", session_id="sid", device_id="dev")
        client.sell(market_id="mid", position_index=0, shares=0.5, session_id="sid", device_id="dev")
        client.post_comment("mid", "reply", parent_comment_id="cid")
        client.edit_comment("cid", "edited")
        client.delete_comment("cid")
        client.like_comment("cid")
        client.follow_user("uid")
        client.unfollow_user("uid")
        client.user_profile("uid")
        client.user_followers("uid")
        client.user_following("uid")
        client.user_balance_history("uid")
        client.user_portfolio_history("uid", tab="closed", sort="pnl")
        client.market_activity("mid", types="comment")
        client.market_charts(["a", "b"])
        client.asset_price("BTC")
        client.balance_transactions(currency="point")
        client.blocked_users()
        client.set_referral_code("S-TEST")
        client.mark_all_notifications_read()
        client.claim_ad_reward()
        client.user_follow_status("uid")
        client.walking_challenge_status()

    assert seen[0][0] == "GET"
    assert "/api/me/profile" in seen[0][1]
    assert seen[0][3]["x-poyp-app-version"] == "1.3.9"
    assert any(method == "POST" and "/api/trades/buy" in url and body["pointAmount"] == 10 for method, url, body, _ in seen)
    assert any(method == "POST" and "/api/trades/sell" in url and body["shares"] == 0.5 for method, url, body, _ in seen)
    assert any(method == "POST" and url.endswith("/api/markets/mid/comments") and body == {"body": "reply", "parentCommentId": "cid"} for method, url, body, _ in seen)
    assert any("/api/markets/charts?ids=a%2Cb&tf=max" in url for _, url, _, _ in seen)


def test_ad_reward_claim_matches_observed_success_shape():
    seen: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(request)
        return httpx.Response(
            200,
            json={
                "earnId": "00000000-0000-0000-0000-000000000000",
                "rewardPoints": 5,
                "pointBalanceAfter": 8,
                "dailyViewCount": 2,
                "dailyViewLimit": 5,
            },
        )

    with isolated_client(access_token="token", transport=httpx.MockTransport(handler)) as client:
        result = client.claim_ad_reward()

    assert seen[0].method == "POST"
    assert seen[0].url.path == "/api/me/ad-rewards/claim"
    assert seen[0].url.params["source"] == "watch_ad"
    assert seen[0].content == b""
    assert result["rewardPoints"] == 5
    assert result["pointBalanceAfter"] == 8
    assert result["dailyViewCount"] == 2
    assert result["dailyViewLimit"] == 5


def test_apple_login_shape(recorder):
    seen, transport = recorder
    with isolated_client(transport=transport) as client:
        session = client.login_with_apple(id_token="id", apple_access_token="apple", nonce="nonce")
    assert session.access_token == "a" * 40
    body = seen[-1][2]
    assert body["provider"] == "apple"
    assert body["access_token"] == "apple"
    assert body["nonce"] == "nonce"


def test_authentication_required():
    transport = httpx.MockTransport(lambda _: httpx.Response(200, json={"ok": True}))
    with isolated_client(transport=transport) as client:
        with pytest.raises(AuthenticationError):
            client.profile()


def test_api_error_exposes_response_details():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(400, json={"error": "bad request"}, request=request)
    with isolated_client(access_token="token", transport=httpx.MockTransport(handler)) as client:
        with pytest.raises(APIError) as exc_info:
            client.profile()
    assert exc_info.value.status_code == 400
    assert exc_info.value.response_body == {"error": "bad request"}
