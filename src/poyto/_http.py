from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
from typing import Any

import httpx

from .config import Settings
from .device_store import DeviceIdStore
from .exceptions import APIError, AuthenticationError
from .models import AuthSession, DeviceInfo


class HTTPClient:
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
        device_file: str | Path | None = None,
        timeout: float | None = None,
        transport: httpx.BaseTransport | None = None,
        api_base: str | None = None,
        auth_base: str | None = None,
    ) -> None:
        settings = Settings.from_env()
        self.api_base = (api_base or settings.api_base or self.API_BASE).rstrip("/")
        self.auth_base = (auth_base or settings.auth_base or self.AUTH_BASE).rstrip("/")
        self.supabase_key = supabase_key or settings.supabase_key or self.DEFAULT_SUPABASE_KEY
        self.device = device or DeviceInfo.from_env()
        self.device_store = DeviceIdStore(device_file or settings.device_file)
        if not self.device.device_id:
            self.device.device_id = self.device_store.get_or_create()
        self.session = AuthSession(access_token, refresh_token) if access_token else None
        self.http = httpx.Client(
            timeout=settings.timeout if timeout is None else timeout,
            follow_redirects=True,
            transport=transport,
            headers={"accept": "application/json", "x-client-info": "Poyto"},
        )

    def __enter__(self) -> HTTPClient:
        return self

    def __exit__(self, *_: Any) -> None:
        self.close()

    def close(self) -> None:
        self.http.close()

    def login_with_apple(
        self,
        *,
        id_token: str,
        apple_access_token: str | None = None,
        nonce: str | None = None,
    ) -> AuthSession:
        payload: dict[str, Any] = {
            "provider": "apple",
            "id_token": id_token,
            "gotrue_meta_security": {},
        }
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

    def request(
        self,
        method: str,
        path: str,
        *,
        params: Mapping[str, Any] | None = None,
        json: Any = None,
        auth: bool = True,
        headers: Mapping[str, str] | None = None,
    ) -> Any:
        normalized = path if path.startswith("/") else f"/{path}"
        request_headers = self._poyp_headers(auth=auth)
        if headers:
            request_headers.update(headers)
        response = self.http.request(
            method.upper(),
            f"{self.api_base}{normalized}",
            params=dict(params) if params else None,
            json=json,
            headers=request_headers,
        )
        return self._decode(response)

    def get(self, path: str, *, params: Mapping[str, Any] | None = None, auth: bool = True) -> Any:
        return self.request("GET", path, params=params, auth=auth)

    def post(self, path: str, *, params: Mapping[str, Any] | None = None, json: Any = None, auth: bool = True) -> Any:
        return self.request("POST", path, params=params, json=json, auth=auth)

    def put(self, path: str, *, params: Mapping[str, Any] | None = None, json: Any = None, auth: bool = True) -> Any:
        return self.request("PUT", path, params=params, json=json, auth=auth)

    def patch(self, path: str, *, params: Mapping[str, Any] | None = None, json: Any = None, auth: bool = True) -> Any:
        return self.request("PATCH", path, params=params, json=json, auth=auth)

    def delete(self, path: str, *, params: Mapping[str, Any] | None = None, json: Any = None, auth: bool = True) -> Any:
        return self.request("DELETE", path, params=params, json=json, auth=auth)

    @staticmethod
    def _cursor_params(params: dict[str, Any], cursor: str | None) -> dict[str, Any]:
        if cursor is not None:
            params["cursor"] = cursor
        return params

    def _auth_header(self) -> dict[str, str]:
        if not self.session:
            raise AuthenticationError("client is not authenticated")
        return {"authorization": f"Bearer {self.session.access_token}"}

    def _supabase_headers(self) -> dict[str, str]:
        return {"apikey": self.supabase_key, "authorization": f"Bearer {self.supabase_key}"}

    def _poyp_headers(self, *, auth: bool) -> dict[str, str]:
        headers = {
            "accept": "application/json",
            "x-poyp-app-version": self.device.app_version,
            "x-poyp-os": self.device.os,
            "x-poyp-is-device": "true" if self.device.is_device else "false",
        }
        optional = {
            "x-poyp-os-version": self.device.os_version,
            "x-poyp-device-model": self.device.device_model,
            "x-poyp-device-id": self.device.device_id,
            "x-poyp-vendor-id": self.device.vendor_id,
            "x-poyp-ota-generation": self.device.ota_generation,
        }
        headers.update({key: value for key, value in optional.items() if value is not None})
        if auth:
            headers.update(self._auth_header())
        return headers

    @staticmethod
    def _decode(response: httpx.Response) -> Any:
        if response.is_success:
            if not response.content:
                return None
            try:
                return response.json()
            except ValueError:
                return response.text
        try:
            body: Any = response.json()
        except ValueError:
            body = response.text[:2000]
        raise APIError(
            f"POYP API returned HTTP {response.status_code}",
            status_code=response.status_code,
            method=response.request.method,
            url=str(response.request.url),
            response_body=body,
        )
