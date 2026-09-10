from __future__ import annotations

import json
import uuid

import httpx

from poyto import DeviceInfo, PoytoClient
from poyto.device_store import DeviceIdStore


def test_device_id_store_generates_uuid_v4_once(tmp_path):
    path = tmp_path / "device.json"
    store = DeviceIdStore(path)

    first = store.get_or_create()
    second = DeviceIdStore(path).get_or_create()

    parsed = uuid.UUID(first)
    assert parsed.version == 4
    assert second == first
    assert json.loads(path.read_text(encoding="utf-8")) == {"poyp_device_id": first}


def test_client_reuses_device_id_in_header_and_trade_after_logout(tmp_path):
    device_path = tmp_path / "device.json"
    session_path = tmp_path / "session.json"
    seen: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(request)
        return httpx.Response(200, json={"ok": True})

    transport = httpx.MockTransport(handler)
    with PoytoClient(
        access_token="token",
        session_file=session_path,
        device_file=device_path,
        auto_load_session=False,
        save_session=False,
        transport=transport,
    ) as client:
        first = client.device.device_id
        client.profile()
        client.buy(market_id="market", position_index=0, point_amount=1)
        client.logout(local_only=True)

    assert first is not None
    assert seen[0].headers["x-poyp-device-id"] == first
    assert json.loads(seen[1].content)["deviceId"] == first

    with PoytoClient(
        access_token="token-2",
        session_file=session_path,
        device_file=device_path,
        auto_load_session=False,
        save_session=False,
        transport=transport,
    ) as client:
        assert client.device.device_id == first


def test_explicit_and_environment_device_ids_override_persistence(monkeypatch, tmp_path):
    device_path = tmp_path / "device.json"
    monkeypatch.setenv("POYTO_DEVICE_ID", "env-device")

    with PoytoClient(
        access_token="token",
        device_file=device_path,
        auto_load_session=False,
        save_session=False,
    ) as client:
        assert client.device.device_id == "env-device"
    assert not device_path.exists()

    with PoytoClient(
        access_token="token",
        device=DeviceInfo(device_id="explicit-device"),
        device_file=device_path,
        auto_load_session=False,
        save_session=False,
    ) as client:
        assert client.device.device_id == "explicit-device"
    assert not device_path.exists()
