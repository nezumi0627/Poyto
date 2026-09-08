from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .models import AuthSession

_ACCESS_KEYS = ("access_token", "POYP_ACCESS_TOKEN", "token")
_REFRESH_KEYS = ("refresh_token", "POYP_REFRESH_TOKEN")


def _first(data: dict[str, Any], keys: tuple[str, ...]) -> Any:
    for key in keys:
        value = data.get(key)
        if value not in (None, ""):
            return value
    return None


def parse_token_text(text: str) -> AuthSession:
    """Parse JSON, .env-style, or simple plaintext token data."""
    stripped = text.strip()
    if not stripped:
        raise ValueError("token source is empty")

    if stripped.startswith("{"):
        data = json.loads(stripped)
        if not isinstance(data, dict):
            raise ValueError("token JSON must be an object")
        access = _first(data, _ACCESS_KEYS)
        if not isinstance(access, str) or not access.strip():
            raise ValueError("token JSON does not contain an access token")
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
        raise ValueError("token source does not contain an access token")

    return AuthSession(
        access_token=access.strip(),
        refresh_token=refresh.strip() if isinstance(refresh, str) and refresh.strip() else None,
    )


def load_token_file(path: str | Path) -> AuthSession:
    return parse_token_text(Path(path).expanduser().read_text(encoding="utf-8-sig"))


def load_token_source(source: str | Path) -> AuthSession:
    """Load a literal token or token file.

    ``Path`` always means a file. A string prefixed with ``@`` or ``file:`` also
    means a file. Other strings are treated as a file only when that path exists;
    otherwise they are treated as a literal access token.
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
        raise ValueError("token is empty")
    return AuthSession(access_token=value)
