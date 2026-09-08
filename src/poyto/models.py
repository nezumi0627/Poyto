from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any, TypedDict


def _env(*names: str) -> str | None:
    for name in names:
        value = os.getenv(name)
        if value not in (None, ""):
            return value
    return None


class AdRewardClaimResponse(TypedDict):
    earnId: str
    rewardPoints: int
    pointBalanceAfter: int
    dailyViewCount: int
    dailyViewLimit: int


@dataclass(slots=True)
class AuthSession:
    access_token: str
    refresh_token: str | None = None
    expires_in: int | None = None
    expires_at: int | None = None
    token_type: str = "bearer"
    user: dict[str, Any] | None = None

    @classmethod
    def from_json(cls, data: dict[str, Any]) -> AuthSession:
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
    def from_env(cls) -> DeviceInfo:
        is_device = _env("POYTO_IS_DEVICE", "POYP_IS_DEVICE") or "true"
        return cls(
            app_version=_env("POYTO_APP_VERSION", "POYP_APP_VERSION") or "1.3.9",
            os=_env("POYTO_OS", "POYP_OS") or "ios",
            os_version=_env("POYTO_OS_VERSION", "POYP_OS_VERSION"),
            device_model=_env("POYTO_DEVICE_MODEL", "POYP_DEVICE_MODEL"),
            device_id=_env("POYTO_DEVICE_ID", "POYP_DEVICE_ID"),
            vendor_id=_env("POYTO_VENDOR_ID", "POYP_VENDOR_ID"),
            ota_generation=_env("POYTO_OTA_GENERATION", "POYP_OTA_GENERATION"),
            is_device=is_device.strip().lower() not in {"0", "false", "no", "off"},
        )
