from __future__ import annotations

import base64
import json
import zipfile
from pathlib import Path
from typing import Any

from .exceptions import CredentialError
from .models import AuthSession

_AUTH_TOKEN_URL = "https://auth.poyp.app/auth/v1/token"


def _response_json(entry: dict[str, Any]) -> dict[str, Any] | None:
    response = entry.get("response")
    if not isinstance(response, dict):
        return None
    content = response.get("content")
    if not isinstance(content, dict):
        return None
    text = content.get("text")
    if not isinstance(text, str) or not text.strip():
        return None
    if content.get("encoding") == "base64":
        try:
            text = base64.b64decode(text).decode("utf-8")
        except (ValueError, UnicodeDecodeError):
            return None
    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        return None
    return data if isinstance(data, dict) else None


def extract_session_from_har(data: dict[str, Any]) -> AuthSession:
    """Extract the newest POYP/Supabase session returned in a HAR capture.

    Only response bodies from POYP's Auth token endpoint are inspected. Request
    bodies are intentionally ignored because Apple's provider request also
    contains a field named ``access_token`` that is not the POYP session token.
    """
    log = data.get("log")
    entries = log.get("entries") if isinstance(log, dict) else None
    if not isinstance(entries, list):
        raise CredentialError("HAR does not contain log.entries")

    for raw_entry in reversed(entries):
        if not isinstance(raw_entry, dict):
            continue
        request = raw_entry.get("request")
        url = request.get("url") if isinstance(request, dict) else None
        if not isinstance(url, str) or not url.startswith(_AUTH_TOKEN_URL):
            continue

        payload = _response_json(raw_entry)
        if payload is None:
            continue
        access = payload.get("access_token")
        refresh = payload.get("refresh_token")
        if not isinstance(access, str) or not access.strip():
            continue
        if not isinstance(refresh, str) or not refresh.strip():
            continue
        return AuthSession.from_json(payload)

    raise CredentialError("HAR does not contain a POYP session response")


def _load_json_bytes(raw: bytes, source: str) -> dict[str, Any]:
    try:
        data = json.loads(raw.decode("utf-8-sig"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise CredentialError(f"invalid HAR JSON: {source}") from exc
    if not isinstance(data, dict):
        raise CredentialError(f"HAR root must be an object: {source}")
    return data


def load_har_session(path: str | Path) -> AuthSession:
    """Load a POYP session from a ``.har`` file or ``.har.zip`` archive."""
    resolved = Path(path).expanduser()
    if not resolved.is_file():
        raise CredentialError(f"HAR file does not exist: {resolved}")

    if resolved.suffix.lower() == ".zip":
        try:
            with zipfile.ZipFile(resolved) as archive:
                names = [name for name in archive.namelist() if name.lower().endswith(".har")]
                if not names:
                    raise CredentialError("HAR zip does not contain a .har file")
                last_error: CredentialError | None = None
                for name in reversed(names):
                    try:
                        return extract_session_from_har(_load_json_bytes(archive.read(name), name))
                    except CredentialError as exc:
                        last_error = exc
                assert last_error is not None
                raise last_error
        except zipfile.BadZipFile as exc:
            raise CredentialError(f"invalid HAR zip: {resolved}") from exc

    try:
        raw = resolved.read_bytes()
    except OSError as exc:
        raise CredentialError(f"cannot read HAR file: {resolved}") from exc
    return extract_session_from_har(_load_json_bytes(raw, str(resolved)))


__all__ = ["extract_session_from_har", "load_har_session"]
