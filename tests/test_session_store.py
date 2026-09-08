from __future__ import annotations

import time

import httpx

from poyto import AuthSession, PoytoClient, SessionStore


def test_session_store_round_trip(tmp_path):
    path = tmp_path / "session.json"
    store = SessionStore(path)
    source = AuthSession(
        access_token="access",
        refresh_token="refresh",
        expires_in=3600,
        expires_at=int(time.time()) + 3600,
        user={"id": "user"},
    )
    store.save(source)
    loaded = store.load()
    assert loaded is not None
    assert loaded.access_token == "access"
    assert loaded.refresh_token == "refresh"
    assert loaded.user == {"id": "user"}
    store.clear()
    assert store.load() is None


def test_client_auto_loads_saved_session(tmp_path):
    path = tmp_path / "session.json"
    SessionStore(path).save(AuthSession(access_token="saved-token", refresh_token="saved-refresh"))
    seen: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(request)
        return httpx.Response(200, json={"ok": True})

    with PoytoClient(session_file=path, transport=httpx.MockTransport(handler)) as client:
        client.profile()

    assert seen[0].headers["authorization"] == "Bearer saved-token"


def test_login_persists_for_next_client(tmp_path):
    path = tmp_path / "session.json"
    with PoytoClient(session_file=path, auto_load_session=False) as client:
        client.login("token-a", "token-r")

    with PoytoClient(session_file=path) as client:
        assert client.session is not None
        assert client.session.access_token == "token-a"
        assert client.session.refresh_token == "token-r"


def test_expired_session_auto_refreshes(tmp_path):
    path = tmp_path / "session.json"
    SessionStore(path).save(
        AuthSession(
            access_token="expired",
            refresh_token="refresh-me",
            expires_at=int(time.time()) - 1,
        )
    )

    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.params["grant_type"] == "refresh_token"
        return httpx.Response(
            200,
            json={
                "access_token": "new-access",
                "refresh_token": "new-refresh",
                "expires_in": 3600,
                "expires_at": int(time.time()) + 3600,
            },
        )

    with PoytoClient(session_file=path, transport=httpx.MockTransport(handler)) as client:
        assert client.session is not None
        assert client.session.access_token == "new-access"

    persisted = SessionStore(path).load()
    assert persisted is not None
    assert persisted.access_token == "new-access"
