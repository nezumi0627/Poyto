from __future__ import annotations

import json
import time

import httpx

from poyto import AuthSession, PoytoClient, SessionStore
from poyto.token_loader import load_token_file, parse_token_text


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


def test_plaintext_token_parser():
    session = parse_token_text("access-token\nrefresh-token\n")
    assert session.access_token == "access-token"
    assert session.refresh_token == "refresh-token"


def test_env_style_token_parser():
    session = parse_token_text(
        "POYP_ACCESS_TOKEN='access-token'\nPOYP_REFRESH_TOKEN=refresh-token\n"
    )
    assert session.access_token == "access-token"
    assert session.refresh_token == "refresh-token"


def test_json_token_parser():
    session = parse_token_text(
        json.dumps(
            {
                "access_token": "access-token",
                "refresh_token": "refresh-token",
                "expires_at": 123,
            }
        )
    )
    assert session.access_token == "access-token"
    assert session.refresh_token == "refresh-token"
    assert session.expires_at == 123


def test_token_file_loader(tmp_path):
    path = tmp_path / "token.txt"
    path.write_text("access-from-file\nrefresh-from-file\n", encoding="utf-8")
    session = load_token_file(path)
    assert session.access_token == "access-from-file"
    assert session.refresh_token == "refresh-from-file"


def test_client_token_literal():
    with PoytoClient(token="literal-token", auto_load_session=False, save_session=False) as client:
        assert client.session is not None
        assert client.session.access_token == "literal-token"


def test_client_token_path(tmp_path):
    path = tmp_path / "token.txt"
    path.write_text("file-token\nfile-refresh\n", encoding="utf-8")
    with PoytoClient(token=path, auto_load_session=False, save_session=False) as client:
        assert client.session is not None
        assert client.session.access_token == "file-token"
        assert client.session.refresh_token == "file-refresh"


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
