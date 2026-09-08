from __future__ import annotations

import os
import time
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from .client import PoytoClient as BasePoytoClient
from .exceptions import APIError
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

        if access_token is not None:
            effective_access = access_token
            effective_refresh = refresh_token
            loaded_stored_session = False
        elif env_access is not None:
            effective_access = env_access
            effective_refresh = env_refresh
            loaded_stored_session = False
        elif stored is not None:
            effective_access = stored.access_token
            effective_refresh = stored.refresh_token
            loaded_stored_session = True
        else:
            effective_access = None
            effective_refresh = None
            loaded_stored_session = False

        super().__init__(
            access_token=effective_access,
            refresh_token=effective_refresh,
            **kwargs,
        )

        if loaded_stored_session and stored and self.session:
            self.session.expires_in = stored.expires_in
            self.session.expires_at = stored.expires_at
            self.session.token_type = stored.token_type

        self._refresh_if_needed()

    @classmethod
    def from_env(cls, **kwargs: Any) -> PoytoClient:
        return cls(**kwargs)

    def __enter__(self) -> PoytoClient:
        return self

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

    def request(
        self,
        method: str,
        path: str,
        *,
        params: Mapping[str, Any] | None = None,
        json: Any = None,
        auth: bool = True,
        headers: Mapping[str, str] | None = None,
    ) -> Any:
        try:
            return super().request(
                method,
                path,
                params=params,
                json=json,
                auth=auth,
                headers=headers,
            )
        except APIError as exc:
            can_retry = (
                auth
                and self.auto_refresh
                and exc.status_code == 401
                and self.session is not None
                and self.session.refresh_token is not None
            )
            if not can_retry:
                raise
            self.refresh()
            return super().request(
                method,
                path,
                params=params,
                json=json,
                auth=auth,
                headers=headers,
            )

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
