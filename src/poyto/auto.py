from __future__ import annotations

import time
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from .client import PoytoClient as BasePoytoClient
from .config import Settings
from .exceptions import APIError
from .har_loader import load_har_session
from .models import AuthSession
from .session_store import SessionStore
from .token_loader import load_token_file, load_token_source


class PoytoClient(BasePoytoClient):
    """High-level client with token loading, persistence, and automatic refresh."""

    def __init__(
        self,
        *,
        token: str | Path | None = None,
        token_file: str | Path | None = None,
        access_token: str | None = None,
        refresh_token: str | None = None,
        session_file: str | Path | None = None,
        auto_load_session: bool | None = None,
        auto_refresh: bool | None = None,
        save_session: bool | None = None,
        **kwargs: Any,
    ) -> None:
        settings = Settings.from_env()
        self.auto_refresh = settings.auto_refresh if auto_refresh is None else auto_refresh
        self.save_session = settings.save_session if save_session is None else save_session
        load_saved = settings.auto_load_session if auto_load_session is None else auto_load_session
        self.session_store = SessionStore(session_file or settings.session_file)
        stored = self.session_store.load() if load_saved else None

        effective_access: str | None
        effective_refresh: str | None
        metadata_source: AuthSession | None = None

        if access_token is not None:
            effective_access = access_token
            effective_refresh = refresh_token
        elif token is not None:
            metadata_source = load_token_source(token)
            effective_access = metadata_source.access_token
            effective_refresh = refresh_token or metadata_source.refresh_token
        elif token_file is not None:
            metadata_source = load_token_file(token_file)
            effective_access = metadata_source.access_token
            effective_refresh = refresh_token or metadata_source.refresh_token
        elif settings.token is not None:
            metadata_source = load_token_source(settings.token)
            effective_access = metadata_source.access_token
            effective_refresh = settings.refresh_token or metadata_source.refresh_token
        elif settings.token_file is not None:
            metadata_source = load_token_file(settings.token_file)
            effective_access = metadata_source.access_token
            effective_refresh = settings.refresh_token or metadata_source.refresh_token
        elif stored is not None:
            metadata_source = stored
            effective_access = stored.access_token
            effective_refresh = refresh_token or stored.refresh_token
        else:
            effective_access = None
            effective_refresh = refresh_token

        super().__init__(
            access_token=effective_access,
            refresh_token=effective_refresh,
            **kwargs,
        )
        self._copy_session_metadata(metadata_source)
        self._refresh_if_needed()

    def _copy_session_metadata(self, source: AuthSession | None) -> None:
        if source is None or self.session is None:
            return
        self.session.expires_in = source.expires_in
        self.session.expires_at = source.expires_at
        self.session.token_type = source.token_type
        self.session.user = source.user

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
        self._copy_session_metadata(source)
        if persist and self.save_session:
            self.session_store.save(self.session)
        return self.session

    def login_file(self, path: str | Path, *, persist: bool = True) -> AuthSession:
        return self.login(Path(path), persist=persist)

    def login_from_har(self, path: str | Path, *, persist: bool = True) -> AuthSession:
        """Import the newest POYP session from a HAR/HAR.zip capture."""
        source = load_har_session(path)
        self.set_access_token(source.access_token, source.refresh_token)
        assert self.session is not None
        self._copy_session_metadata(source)
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
        include_poyp_headers: bool = True,
    ) -> Any:
        try:
            return super().request(
                method,
                path,
                params=params,
                json=json,
                auth=auth,
                headers=headers,
                include_poyp_headers=include_poyp_headers,
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
                include_poyp_headers=include_poyp_headers,
            )

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
