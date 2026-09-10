from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

_DEFAULT_API_BASE = "https://api.poyp.app"
_DEFAULT_AUTH_BASE = "https://auth.poyp.app"
_DEFAULT_TIMEOUT = 20.0


def env_value(*names: str) -> str | None:
    for name in names:
        value = os.getenv(name)
        if value not in (None, ""):
            return value
    return None


def env_bool(*names: str, default: bool) -> bool:
    value = env_value(*names)
    if value is None:
        return default
    return value.strip().lower() not in {"0", "false", "no", "off"}


def env_float(*names: str, default: float) -> float:
    value = env_value(*names)
    if value is None:
        return default
    try:
        return float(value)
    except ValueError:
        return default


@dataclass(frozen=True, slots=True)
class Settings:
    """Environment-backed configuration used throughout Poyto.

    ``POYTO_*`` variables are canonical. ``POYP_*`` credential/device aliases are
    accepted for compatibility with earlier releases and existing scripts.
    Explicit Python/CLI arguments always take precedence.
    """

    api_base: str = _DEFAULT_API_BASE
    auth_base: str = _DEFAULT_AUTH_BASE
    timeout: float = _DEFAULT_TIMEOUT
    supabase_key: str | None = None
    token: str | None = None
    refresh_token: str | None = None
    token_file: Path | None = None
    session_file: Path | None = None
    device_file: Path | None = None
    auto_load_session: bool = True
    auto_refresh: bool = True
    save_session: bool = True
    apple_id_token: str | None = None
    apple_access_token: str | None = None
    apple_nonce: str | None = None

    @classmethod
    def from_env(cls) -> Settings:
        token_file = env_value("POYTO_TOKEN_FILE", "POYP_TOKEN_FILE")
        session_file = env_value("POYTO_SESSION_FILE")
        device_file = env_value("POYTO_DEVICE_FILE", "POYP_DEVICE_FILE")
        return cls(
            api_base=env_value("POYTO_API_BASE", "POYP_API_BASE") or _DEFAULT_API_BASE,
            auth_base=env_value("POYTO_AUTH_BASE", "POYP_AUTH_BASE") or _DEFAULT_AUTH_BASE,
            timeout=env_float("POYTO_TIMEOUT", "POYP_TIMEOUT", default=_DEFAULT_TIMEOUT),
            supabase_key=env_value("POYTO_SUPABASE_KEY", "POYP_SUPABASE_KEY"),
            token=env_value("POYTO_TOKEN", "POYTO_ACCESS_TOKEN", "POYP_ACCESS_TOKEN"),
            refresh_token=env_value("POYTO_REFRESH_TOKEN", "POYP_REFRESH_TOKEN"),
            token_file=Path(token_file).expanduser() if token_file else None,
            session_file=Path(session_file).expanduser() if session_file else None,
            device_file=Path(device_file).expanduser() if device_file else None,
            auto_load_session=env_bool("POYTO_AUTO_LOAD_SESSION", default=True),
            auto_refresh=env_bool("POYTO_AUTO_REFRESH", default=True),
            save_session=env_bool("POYTO_SAVE_SESSION", default=True),
            apple_id_token=env_value("POYTO_APPLE_ID_TOKEN", "POYP_APPLE_ID_TOKEN"),
            apple_access_token=env_value(
                "POYTO_APPLE_ACCESS_TOKEN",
                "POYP_APPLE_ACCESS_TOKEN",
            ),
            apple_nonce=env_value("POYTO_APPLE_NONCE", "POYP_APPLE_NONCE"),
        )


__all__ = ["Settings", "env_bool", "env_float", "env_value"]
