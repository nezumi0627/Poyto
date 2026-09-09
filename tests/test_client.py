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


def test_loss_gacha_flow_matches_observed_shapes():
    seen: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(request)
        if request.url.path.endswith("/status"):
            return httpx.Response(
                200,
                json={
                    "mode": "gacha_mini",
                    "reason": None,
                    "gachaExpiresAt": "2026-09-09T21:04:16.783Z",
                    "publicRange": {"min": 5, "max": 10},
                },
            )
        if request.url.path.endswith("/ticket"):
            return httpx.Response(
                200,
                json={
                    "ticketId": "00000000-0000-0000-0000-000000000001",
                    "expiresAt": "2026-09-09T04:04:09+00:00",
                },
            )
        return httpx.Response(
            200,
            json={
                "grantedPoints": 10,
                "grantedCoins": 0,
                "roll": "jackpot",
                "balanceAfter": 20,
            },
        )

    with isolated_client(access_token="token", transport=httpx.MockTransport(handler)) as client:
        status = client.loss_gacha_status("market-id")
        ticket = client.create_loss_gacha_ticket("market-id")
        claim = client.claim_loss_gacha(
            "market-id",
            ticket["ticketId"],
            kind="video_gacha",
        )

    assert seen[0].method == "GET"
    assert seen[0].url.path == "/api/me/loss-gacha/status"
    assert seen[0].url.params["marketId"] == "market-id"
    assert seen[1].method == "POST"
    assert seen[1].url.path == "/api/me/loss-gacha/ticket"
    assert json.loads(seen[1].content) == {"marketId": "market-id"}
    assert seen[2].method == "POST"
    assert seen[2].url.path == "/api/me/loss-gacha/claim"
    assert json.loads(seen[2].content) == {
        "marketId": "market-id",
        "kind": "video_gacha",
        "ticketId": "00000000-0000-0000-0000-000000000001",
    }
    assert status["mode"] == "gacha_mini"
    assert status["publicRange"] == {"min": 5, "max": 10}
    assert ticket["ticketId"] == "00000000-0000-0000-0000-000000000001"
    assert claim["grantedPoints"] == 10
    assert claim["roll"] == "jackpot"
    assert claim["balanceAfter"] == 20


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


def test_health_matches_current_android_public_request_shape() -> None:
    seen: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(request)
        return httpx.Response(200, json={"ok": True})

    device = DeviceInfo(
        app_version="1.3.9",
        os="android",
        os_version="16",
        ota_generation="1030905",
        is_device=False,
    )
    with isolated_client(device=device, transport=httpx.MockTransport(handler)) as client:
        client.health()

    request = seen[0]
    assert request.method == "GET"
    assert request.url.path == "/api/health"
    assert "authorization" not in request.headers
    assert request.headers["x-poyp-ota-generation"] == "1030905"
    assert "x-poyp-app-version" not in request.headers
    assert "x-poyp-os" not in request.headers
    assert "x-poyp-os-version" not in request.headers
    assert "x-poyp-is-device" not in request.headers
