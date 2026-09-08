from __future__ import annotations

from typing import Any


class PoytoError(RuntimeError):
    """Base exception for the unofficial POYP client."""


class AuthenticationError(PoytoError):
    """Raised when authentication credentials are missing or rejected."""


class APIError(PoytoError):
    """Raised when the POYP API returns a non-success response."""

    def __init__(
        self,
        message: str,
        *,
        status_code: int | None = None,
        method: str | None = None,
        url: str | None = None,
        response_body: Any = None,
    ) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.method = method
        self.url = url
        self.response_body = response_body
