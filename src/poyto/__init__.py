from .auto import PoytoClient
from .exceptions import APIError, AuthenticationError, PoytoError
from .models import AuthSession, DeviceInfo
from .session_store import SessionStore, default_session_path
from .token_loader import load_token_file, load_token_source, parse_token_text

__all__ = [
    "APIError",
    "AuthSession",
    "AuthenticationError",
    "DeviceInfo",
    "PoytoClient",
    "PoypClient",
    "PoytoError",
    "PoypError",
    "SessionStore",
    "default_session_path",
    "load_token_file",
    "load_token_source",
    "parse_token_text",
]

__version__ = "0.1.0"

# Backward compatibility with early development snapshots.
PoypClient = PoytoClient
PoypError = PoytoError
