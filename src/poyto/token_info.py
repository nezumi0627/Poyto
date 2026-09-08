from __future__ import annotations

from dataclasses import asdict, dataclass

from .models import AuthSession


@dataclass(slots=True, frozen=True)
class SessionInfo:
    authenticated: bool
    access_token_kind: str | None
    has_refresh_token: bool
    refresh_token_kind: str | None
    expires_in: int | None
    expires_at: int | None
    user_id: str | None

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


def token_kind(token: str | None) -> str | None:
    if not token:
        return None
    return "jwt" if len(token.split(".")) == 3 else "opaque"


def session_info(session: AuthSession | None) -> SessionInfo:
    if session is None:
        return SessionInfo(False, None, False, None, None, None, None)
    user_id = (session.user or {}).get("id")
    return SessionInfo(
        authenticated=True,
        access_token_kind=token_kind(session.access_token),
        has_refresh_token=bool(session.refresh_token),
        refresh_token_kind=token_kind(session.refresh_token),
        expires_in=session.expires_in,
        expires_at=session.expires_at,
        user_id=user_id if isinstance(user_id, str) else None,
    )


__all__ = ["SessionInfo", "session_info", "token_kind"]
