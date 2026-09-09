from __future__ import annotations

import json
import os
from collections.abc import Iterator
from contextlib import contextmanager
from importlib import import_module
from pathlib import Path
from typing import Any

from .models import AuthSession


def default_session_path() -> Path:
    override = os.getenv("POYTO_SESSION_FILE")
    if override:
        return Path(override).expanduser()

    if os.name == "nt":
        base = Path(os.getenv("LOCALAPPDATA") or Path.home() / "AppData" / "Local")
        return base / "Poyto" / "session.json"

    xdg = os.getenv("XDG_STATE_HOME")
    base = Path(xdg).expanduser() if xdg else Path.home() / ".local" / "state"
    return base / "poyto" / "session.json"


class SessionStore:
    """Small local store for a POYP session.

    The file location can be overridden with ``POYTO_SESSION_FILE``.
    Tokens are never written to the repository or current working directory by default.
    """

    def __init__(self, path: str | Path | None = None) -> None:
        self.path = Path(path).expanduser() if path else default_session_path()

    def load(self) -> AuthSession | None:
        try:
            data = json.loads(self.path.read_text(encoding="utf-8"))
        except (FileNotFoundError, json.JSONDecodeError, OSError):
            return None
        if not isinstance(data, dict) or not data.get("access_token"):
            return None
        return AuthSession.from_json(data)

    def save(self, session: AuthSession) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        payload: dict[str, Any] = {
            "access_token": session.access_token,
            "refresh_token": session.refresh_token,
            "expires_in": session.expires_in,
            "expires_at": session.expires_at,
            "token_type": session.token_type,
            "user": session.user,
        }
        temp = self.path.with_suffix(self.path.suffix + ".tmp")
        temp.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        try:
            os.chmod(temp, 0o600)
        except OSError:
            pass
        temp.replace(self.path)

    def clear(self) -> None:
        try:
            self.path.unlink()
        except FileNotFoundError:
            pass

    @contextmanager
    def refresh_lock(self) -> Iterator[None]:
        """Serialize refresh-token rotation across local Poyto processes."""
        lock_path = self.path.with_suffix(self.path.suffix + ".lock")
        lock_path.parent.mkdir(parents=True, exist_ok=True)
        with lock_path.open("a+b") as handle:
            if os.name == "nt":
                msvcrt: Any = import_module("msvcrt")

                handle.seek(0, os.SEEK_END)
                if handle.tell() == 0:
                    handle.write(b"\0")
                    handle.flush()
                handle.seek(0)
                msvcrt.locking(handle.fileno(), msvcrt.LK_LOCK, 1)
                try:
                    yield
                finally:
                    handle.seek(0)
                    msvcrt.locking(handle.fileno(), msvcrt.LK_UNLCK, 1)
            else:
                fcntl: Any = import_module("fcntl")

                fcntl.flock(handle.fileno(), fcntl.LOCK_EX)
                try:
                    yield
                finally:
                    fcntl.flock(handle.fileno(), fcntl.LOCK_UN)
