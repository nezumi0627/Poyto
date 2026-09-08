from __future__ import annotations

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
        normalized = dict(data)
        normalized["access_token"] = access.strip()
        refresh = _first(data, _REFRESH_KEYS)
        if isinstance(refresh, str) and refresh.strip():
            normalized["refresh_token"] = refresh.strip()
        return AuthSession.from_json(normalized)

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

    return AuthSession(
        access_token=access.strip(),
        refresh_token=refresh.strip() if isinstance(refresh, str) and refresh.strip() else None,
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
    return AuthSession(access_token=value)


__all__ = ["load_token_file", "load_token_source", "parse_token_text"]
