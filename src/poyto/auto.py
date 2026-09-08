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
from .token_loader import load_token_file, load_token_source


class PoytoClient(BasePoytoClient):
    """Poyto client with automatic token loading, refresh, and persistence."""

    def __init__(
        self,
        *,
        token: str | Path | None = None,
        token_file: str | Path | None = None,
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
        env_token_file = os.getenv("POYTO_TOKEN_FILE") or os.getenv("POYP_TOKEN_FILE")
        stored = self.session_store.load() if auto_load_session else None

        source_session: AuthSession | None = None
        if token is not None:
            source_session = load_token_source(token)
        elif token_file is not None:
            source_session = load_token_file(token_file)
        elif access_token is None and env_access is None and env_token_file:
            source_session = load_token_file(env_token_file)

        if access_token is not None:
            effective_access = access_token
            effective_refresh = refresh_token
            loaded_stored_session = False
        elif source_session is not None:
            effective_access = source_session.access_token
            effective_refresh = refresh_token or source_session.refresh_token
            loaded_stored_session = False
        elif env_access is not None:
            effective_access = env_access
            effective_refresh = refresh_token or env_refresh
            loaded_stored_session = False
        elif stored is not None:
            effective_access = stored.access_token
            effective_refresh = refresh_token or stored.refresh_token
            loaded_stored_session = True
        else:
            effective_access = None
            effective_refresh = refresh_token
            loaded_stored_session = False

        super().__init__(
            access_token=effective_access,
            refresh_token=effective_refresh,
            **kwargs,
        )

        metadata_source = stored if loaded_stored_session else source_session
        if metadata_source and self.session:
            self.session.expires_in = metadata_source.expires_in
            self.session.expires_at = metadata_source.expires_at
            self.session.token_type = metadata_source.token_type

        self._refresh_if_needed()

    @classmethod
    def from_env(cls, **kwargs: Any) -> PoytoClient:
        return cls(**kwargs)

    def __enter__(self) -> PoytoClient:
        return self

    def login(
        self,
        token: str | Path,
        refresh_token: str | None = None,
        *,
        persist: bool = True,
    ) -> AuthSession:
        source = load_token_source(token)
        self.set_access_token(source.access_token, refresh_token or source.refresh_token)
        assert self.session is not None
        self.session.expires_in = source.expires_in
        self.session.expires_at = source.expires_at
        self.session.token_type = source.token_type
        if persist and self.save_session:
            self.session_store.save(self.session)
        return self.session

    def login_file(
        self,
        path: str | Path,
        *,
        persist: bool = True,
    ) -> AuthSession:
        return self.login(Path(path), persist=persist)

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
