from __future__ import annotations

import json
import os
import uuid
from pathlib import Path

_DEVICE_ID_KEY = "poyp_device_id"


def default_device_path() -> Path:
    override = os.getenv("POYTO_DEVICE_FILE") or os.getenv("POYP_DEVICE_FILE")
    if override:
        return Path(override).expanduser()

    if os.name == "nt":
        base = Path(os.getenv("LOCALAPPDATA") or Path.home() / "AppData" / "Local")
        return base / "Poyto" / "device.json"

    xdg = os.getenv("XDG_STATE_HOME")
    base = Path(xdg).expanduser() if xdg else Path.home() / ".local" / "state"
    return base / "poyto" / "device.json"


class DeviceIdStore:
    """Persistent app-style device identifier, separate from the auth session."""

    def __init__(self, path: str | Path | None = None) -> None:
        self.path = Path(path).expanduser() if path else default_device_path()

    def load(self) -> str | None:
        try:
            data = json.loads(self.path.read_text(encoding="utf-8"))
        except (FileNotFoundError, json.JSONDecodeError, OSError):
            return None
        if not isinstance(data, dict):
            return None
        value = data.get(_DEVICE_ID_KEY)
        return value if isinstance(value, str) and value.strip() else None

    def save(self, device_id: str) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        temp = self.path.with_suffix(self.path.suffix + ".tmp")
        temp.write_text(
            json.dumps({_DEVICE_ID_KEY: device_id}, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        try:
            os.chmod(temp, 0o600)
        except OSError:
            pass
        temp.replace(self.path)

    def get_or_create(self) -> str:
        stored = self.load()
        if stored is not None:
            return stored
        device_id = str(uuid.uuid4())
        self.save(device_id)
        return device_id


__all__ = ["DeviceIdStore", "default_device_path"]
