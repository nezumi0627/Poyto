from .client import PoytoClient
from .exceptions import APIError, AuthenticationError, PoytoError
from .models import AuthSession, DeviceInfo

__all__ = [
    "APIError",
    "AuthSession",
    "AuthenticationError",
    "DeviceInfo",
    "PoytoClient",
    "PoypClient",
    "PoytoError",
    "PoypError",
]

__version__ = "0.1.0"

# Backward compatibility with early development snapshots.
PoypClient = PoytoClient
PoypError = PoytoError
