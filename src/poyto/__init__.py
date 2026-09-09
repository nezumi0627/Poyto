from .auto import PoytoClient
from .config import Settings
from .exceptions import APIError, AuthenticationError, CredentialError, PoytoError
from .models import AdRewardClaimResponse, AuthSession, DeviceInfo, LoginBonusStatus
from .session_store import SessionStore, default_session_path
from .token_info import SessionInfo, session_info, token_kind
from .token_loader import load_token_file, load_token_source, parse_token_text

__all__ = [
    "APIError",
    "AdRewardClaimResponse",
    "AuthSession",
    "AuthenticationError",
    "CredentialError",
    "DeviceInfo",
    "LoginBonusStatus",
    "PoytoClient",
    "PoytoError",
    "SessionInfo",
    "SessionStore",
    "Settings",
    "default_session_path",
    "load_token_file",
    "load_token_source",
    "parse_token_text",
    "session_info",
    "token_kind",
    "PoypClient",
    "PoypError",
]

__version__ = "0.2.0"

# Backward compatibility with early development snapshots.
PoypClient = PoytoClient
PoypError = PoytoError
