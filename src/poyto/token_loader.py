from __future__ import annotations

import base64
import json
from pathlib import Path
from typing import Any

from .exceptions import CredentialError
from .models import AuthSession

_ACCESS_KEYS = (
    "access_token",
    "token",
    "POYTO_TOKEN",
    "POYTO_ACCESS_TOKEN",
    "POYP_ACCESS_TOKEN",
)
_REFRESH_KEYS = (
    "refresh_token",
    "POYTO_REFRESH_TOKEN",
    "POYP_REFRESH_TOKEN",
)


def _first(data: dict[str, Any], keys: tuple[str, ...]) -> Any:
    for key in keys:
        value = data.get(key)
        if value not in (None, ""):
            return value
    return None


def _jwt_claims(token: str) -> dict[str, Any] | None:
    """Decode JWT claims for local metadata only; this does not verify trust."""
    parts = token.split(".")
    if len(parts) != 3:
        return None
    try:
        payload = parts[1] + "=" * (-len(parts[1]) % 4)
        decoded = json.loads(base64.urlsafe_b64decode(payload).decode("utf-8"))
    except (ValueError, UnicodeDecodeError, json.JSONDecodeError):
        return None
    return decoded if isinstance(decoded, dict) else None


def _session(access: str, refresh: str | None = None, **metadata: Any) -> AuthSession:
    claims = _jwt_claims(access)
    expires_at = metadata.get("expires_at")
    if expires_at is None and claims is not None and isinstance(claims.get("exp"), int):
        expires_at = claims["exp"]

    expires_in = metadata.get("expires_in")
    if (
        expires_in is None
        and claims is not None
        and isinstance(claims.get("exp"), int)
        and isinstance(claims.get("iat"), int)
    ):
        expires_in = claims["exp"] - claims["iat"]

    return AuthSession(
        access_token=access,
        refresh_token=refresh,
        expires_in=expires_in,
        expires_at=expires_at,
        token_type=metadata.get("token_type", "bearer"),
        user=metadata.get("user"),
    )


def parse_token_text(text: str) -> AuthSession:
    """Parse JSON, dotenv-style, or plain text credential data."""
    stripped = text.strip()
    if not stripped:
        raise CredentialError("token source is empty")

    if stripped.startswith("{"):
        try:
            data = json.loads(stripped)
        except json.JSONDecodeError as exc:
            raise CredentialError("token JSON is invalid") from exc
        if not isinstance(data, dict):
            raise CredentialError("token JSON must be an object")
        access = _first(data, _ACCESS_KEYS)
        if not isinstance(access, str) or not access.strip():
            raise CredentialError("token JSON does not contain an access token")
        refresh = _first(data, _REFRESH_KEYS)
        return _session(
            access.strip(),
            refresh.strip() if isinstance(refresh, str) and refresh.strip() else None,
            expires_in=data.get("expires_in"),
            expires_at=data.get("expires_at"),
            token_type=data.get("token_type", "bearer"),
            user=data.get("user"),
        )

    values: dict[str, str] = {}
    plain: list[str] = []
    for raw_line in stripped.splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" in line:
            key, value = line.split("=", 1)
            key = key.strip()
            value = value.strip().strip('"').strip("'")
            if key:
                values[key] = value
                continue
        plain.append(line)

    access = _first(values, _ACCESS_KEYS)
    refresh = _first(values, _REFRESH_KEYS)
    if access is None and plain:
        access = plain[0]
        if refresh is None and len(plain) > 1:
            refresh = plain[1]

    if not isinstance(access, str) or not access.strip():
        raise CredentialError("token source does not contain an access token")

    return _session(
        access.strip(),
        refresh.strip() if isinstance(refresh, str) and refresh.strip() else None,
    )


def load_token_file(path: str | Path) -> AuthSession:
    resolved = Path(path).expanduser()
    try:
        text = resolved.read_text(encoding="utf-8-sig")
    except OSError as exc:
        raise CredentialError(f"cannot read token file: {resolved}") from exc
    return parse_token_text(text)


def load_token_source(source: str | Path) -> AuthSession:
    """Load a literal token or file reference.

    ``Path`` always means file input. Prefixes ``@`` and ``file:`` force file
    loading. An unprefixed string is treated as a file only when that path exists.
    """
    if isinstance(source, Path):
        return load_token_file(source)
    if source.startswith("@"):
        return load_token_file(source[1:])
    if source.startswith("file:"):
        return load_token_file(source[5:])

    try:
        candidate = Path(source).expanduser()
        if candidate.is_file():
            return load_token_file(candidate)
    except OSError:
        pass

    value = source.strip()
    if not value:
        raise CredentialError("token is empty")
    return _session(value)


__all__ = ["load_token_file", "load_token_source", "parse_token_text"]
