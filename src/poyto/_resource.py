from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from .models import DeviceInfo


class ResourceMixin:
    """Typing contract shared by resource mixins.

    ``PoytoClient`` places the concrete HTTP transport before resource mixins in
    the MRO, so these methods are type declarations only and are never invoked.
    """

    device: DeviceInfo

    def get(
        self,
        path: str,
        *,
        params: Mapping[str, Any] | None = None,
        auth: bool = True,
        headers: Mapping[str, str] | None = None,
        include_poyp_headers: bool = True,
    ) -> Any:
        raise NotImplementedError

    def post(
        self,
        path: str,
        *,
        params: Mapping[str, Any] | None = None,
        json: Any = None,
        auth: bool = True,
    ) -> Any:
        raise NotImplementedError

    def put(
        self,
        path: str,
        *,
        params: Mapping[str, Any] | None = None,
        json: Any = None,
        auth: bool = True,
    ) -> Any:
        raise NotImplementedError

    def patch(
        self,
        path: str,
        *,
        params: Mapping[str, Any] | None = None,
        json: Any = None,
        auth: bool = True,
    ) -> Any:
        raise NotImplementedError

    def delete(
        self,
        path: str,
        *,
        params: Mapping[str, Any] | None = None,
        json: Any = None,
        auth: bool = True,
    ) -> Any:
        raise NotImplementedError

    @staticmethod
    def _cursor_params(params: dict[str, Any], cursor: str | None) -> dict[str, Any]:
        if cursor is not None:
            params["cursor"] = cursor
        return params
