from .auto import PoytoClient
from .config import Settings
from .exceptions import APIError, AuthenticationError, CredentialError, PoytoError
from .models import AuthSession, DeviceInfo
from .session_store import SessionStore, default_session_path
from .token_loader import load_token_file, load_token_source, parse_token_text

__all__ = [
    "APIError",
    "AuthSession",
    "AuthenticationError",
    "CredentialError",
    "DeviceInfo",
    "PoytoClient",
    "PoytoError",
    "SessionStore",
    "Settings",
    "default_session_path",
    "load_token_file",
    "load_token_source",
    "parse_token_text",
    "PoypClient",
    "PoypError",
]

__version__ = "0.2.0"

# Backward compatibility with early development snapshots.
PoypClient = PoytoClient
PoypError = PoytoError
