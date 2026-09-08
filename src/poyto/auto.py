from __future__ import annotations

import os
import time
from pathlib import Path
from typing import Any

from .client import PoytoClient as BasePoytoClient
from .models import AuthSession
from .session_store import SessionStore


class PoytoClient(BasePoytoClient):
    """Poyto client with automatic local session loading and persistence."""

    def __init__(
        self,
        *,
        access_token: str | None = None,
        refresh_token: str | None = None,
        session_file: str | Path | None = None,
        auto_load_session: bool = True,
        auto_refresh: bool = True,
        save_session: bool = True,
        **kwargs: Any,
    ) -> None:
        self.session_store = SessionStore(session_file)
        self.auto_refresh = auto_refresh
        self.save_session = save_session

        env_access = os.getenv("POYP_ACCESS_TOKEN")
        env_refresh = os.getenv("POYP_REFRESH_TOKEN")
        stored = self.session_store.load() if auto_load_session else None

        effective_access = access_token or env_access or (stored.access_token if stored else None)
        effective_refresh = refresh_token or env_refresh or (stored.refresh_token if stored else None)

        super().__init__(
            access_token=effective_access,
            refresh_token=effective_refresh,
            **kwargs,
        )

        if stored and effective_access == stored.access_token and self.session:
            self.session.expires_in = stored.expires_in
            self.session.expires_at = stored.expires_at
            self.session.token_type = stored.token_type
            self.session.user = stored.user

        self._refresh_if_needed()

    @classmethod
    def from_env(cls, **kwargs: Any) -> PoytoClient:
        return cls(**kwargs)

    def login(
        self,
        access_token: str,
        refresh_token: str | None = None,
        *,
        persist: bool = True,
    ) -> AuthSession:
        self.set_access_token(access_token, refresh_token)
        assert self.session is not None
        if persist and self.save_session:
            self.session_store.save(self.session)
        return self.session

    def login_with_apple(
        self,
        *,
        id_token: str,
        apple_access_token: str | None = None,
        nonce: str | None = None,
    ) -> AuthSession:
        session = super().login_with_apple(
            id_token=id_token,
            apple_access_token=apple_access_token,
            nonce=nonce,
        )
        if self.save_session:
            self.session_store.save(session)
        return session

    def refresh(self, refresh_token: str | None = None) -> AuthSession:
        session = super().refresh(refresh_token)
        if self.save_session:
            self.session_store.save(session)
        return session

    def set_access_token(self, access_token: str, refresh_token: str | None = None) -> None:
        super().set_access_token(access_token, refresh_token)

    def logout(self, scope: str = "global", *, local_only: bool = False) -> None:
        if not local_only and self.session:
            super().logout(scope)
        else:
            self.session = None
        self.session_store.clear()

    def _refresh_if_needed(self) -> None:
        if not self.auto_refresh or not self.session or not self.session.refresh_token:
            return
        expires_at = self.session.expires_at
        if expires_at is not None and expires_at <= int(time.time()) + 60:
            self.refresh()
