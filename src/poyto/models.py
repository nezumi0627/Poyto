from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any


@dataclass(slots=True)
class AuthSession:
    access_token: str
    refresh_token: str | None = None
    expires_in: int | None = None
    expires_at: int | None = None
    token_type: str = "bearer"
    user: dict[str, Any] | None = None

    @classmethod
    def from_json(cls, data: dict[str, Any]) -> "AuthSession":
        return cls(
            access_token=data["access_token"],
            refresh_token=data.get("refresh_token"),
            expires_in=data.get("expires_in"),
            expires_at=data.get("expires_at"),
            token_type=data.get("token_type", "bearer"),
            user=data.get("user"),
        )


@dataclass(slots=True)
class DeviceInfo:
    app_version: str = "1.3.9"
    os: str = "ios"
    os_version: str | None = None
    device_model: str | None = None
    device_id: str | None = None
    vendor_id: str | None = None
    ota_generation: str | None = None
    is_device: bool = True

    @classmethod
    def from_env(cls) -> "DeviceInfo":
        return cls(
            app_version=os.getenv("POYP_APP_VERSION", "1.3.9"),
            os=os.getenv("POYP_OS", "ios"),
            os_version=os.getenv("POYP_OS_VERSION"),
            device_model=os.getenv("POYP_DEVICE_MODEL"),
            device_id=os.getenv("POYP_DEVICE_ID"),
            vendor_id=os.getenv("POYP_VENDOR_ID"),
            ota_generation=os.getenv("POYP_OTA_GENERATION"),
            is_device=os.getenv("POYP_IS_DEVICE", "true").lower()
            not in {"0", "false", "no"},
        )
