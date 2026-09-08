from __future__ import annotations

import httpx

from poyto import PoytoClient
from poyto.config import Settings


def test_environment_token_precedence(monkeypatch, tmp_path):
    monkeypatch.setenv("POYTO_TOKEN", "env-access")
    monkeypatch.setenv("POYTO_REFRESH_TOKEN", "env-refresh")
    monkeypatch.setenv("POYTO_SESSION_FILE", str(tmp_path / "session.json"))
    with PoytoClient(auto_load_session=False) as client:
        assert client.session is not None
        assert client.session.access_token == "env-access"
        assert client.session.refresh_token == "env-refresh"


def test_explicit_token_does_not_mix_environment_refresh(monkeypatch, tmp_path):
    monkeypatch.setenv("POYTO_REFRESH_TOKEN", "env-refresh")
    with PoytoClient(
        token="explicit-access",
        session_file=tmp_path / "session.json",
        auto_load_session=False,
    ) as client:
        assert client.session is not None
        assert client.session.access_token == "explicit-access"
        assert client.session.refresh_token is None


def test_token_file_from_environment(monkeypatch, tmp_path):
    token_file = tmp_path / "token.txt"
    token_file.write_text("file-access\nfile-refresh\n", encoding="utf-8")
    monkeypatch.setenv("POYTO_TOKEN_FILE", str(token_file))
    with PoytoClient(auto_load_session=False) as client:
        assert client.session is not None
        assert client.session.access_token == "file-access"
        assert client.session.refresh_token == "file-refresh"


def test_api_configuration_from_environment(monkeypatch):
    monkeypatch.setenv("POYTO_API_BASE", "https://example.test/api")
    monkeypatch.setenv("POYTO_AUTH_BASE", "https://example.test/auth")
    monkeypatch.setenv("POYTO_TIMEOUT", "7.5")
    settings = Settings.from_env()
    assert settings.api_base == "https://example.test/api"
    assert settings.auth_base == "https://example.test/auth"
    assert settings.timeout == 7.5


def test_asset_price_uses_observed_plural_path(tmp_path):
    seen: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(request)
        return httpx.Response(200, json={"ok": True})

    with PoytoClient(
        token="token",
        session_file=tmp_path / "session.json",
        auto_load_session=False,
        transport=httpx.MockTransport(handler),
    ) as client:
        client.asset_price("BTC")

    assert seen[0].url.path == "/api/prices/BTC"
