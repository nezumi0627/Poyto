from __future__ import annotations

import uuid
from collections.abc import Mapping, Sequence
from datetime import datetime, timezone
from typing import Any

from .._resource import ResourceMixin


class EventsMixin(ResourceMixin):
    def send_events(self, events: Sequence[Mapping[str, Any]]) -> Any:
        return self.post("/api/events", json={"events": list(events)})

    def make_event(
        self,
        event_name: str,
        payload: Mapping[str, Any],
        *,
        event_version: int = 1,
        event_id: str | None = None,
        session_id: str | None = None,
        device_id: str | None = None,
    ) -> dict[str, Any]:
        return {
            "event_id": event_id or str(uuid.uuid4()),
            "event_name": event_name,
            "event_version": event_version,
            "occurred_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            "session_id": session_id or str(uuid.uuid4()),
            "device_id": device_id or self.device.device_id or str(uuid.uuid4()),
            "app_version": self.device.app_version,
            "platform": self.device.os,
            "payload": dict(payload),
        }
