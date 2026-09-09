from __future__ import annotations

import json
import zipfile

import pytest

from poyto import PoytoClient
from poyto.exceptions import CredentialError
from poyto.har_loader import extract_session_from_har, load_har_session
from poyto.session_store import SessionStore


def _har(access: str = "session-access", refresh: str = "session-refresh") -> dict[str, object]:
    return {
        "log": {
            "entries": [
                {
                    "request": {
                        "url": "https://auth.poyp.app/auth/v1/token?grant_type=id_token",
                        "postData": {
                            "text": json.dumps(
                                {
                                    "provider": "apple",
                                    "access_token": "apple-provider-code",
                                }
                            )
                        },
                    },
                    "response": {
                        "content": {
                            "mimeType": "application/json",
                            "text": json.dumps(
                                {
                                    "access_token": access,
                                    "refresh_token": refresh,
                                    "expires_in": 3600,
                                    "expires_at": 1790000000,
                                    "token_type": "bearer",
                                    "user": {"id": "user-1"},
                                }
                            ),
                        }
                    },
                }
            ]
        }
    }


def test_extract_session_uses_response_not_apple_request_token() -> None:
    session = extract_session_from_har(_har())
    assert session.access_token == "session-access"
    assert session.refresh_token == "session-refresh"
    assert session.user == {"id": "user-1"}


def test_load_har_and_zip(tmp_path) -> None:
    raw = json.dumps(_har("access-2", "refresh-2"))
    har_path = tmp_path / "capture.har"
    har_path.write_text(raw, encoding="utf-8")
    assert load_har_session(har_path).refresh_token == "refresh-2"

    zip_path = tmp_path / "capture.har.zip"
    with zipfile.ZipFile(zip_path, "w") as archive:
        archive.writestr("capture.har", raw)
    assert load_har_session(zip_path).access_token == "access-2"


def test_login_from_har_persists_session(tmp_path) -> None:
    har_path = tmp_path / "capture.har"
    har_path.write_text(json.dumps(_har()), encoding="utf-8")
    session_path = tmp_path / "session.json"

    with PoytoClient(
        session_file=session_path,
        auto_load_session=False,
        auto_refresh=False,
    ) as client:
        session = client.login_from_har(har_path)

    stored = SessionStore(session_path).load()
    assert session.refresh_token == "session-refresh"
    assert stored is not None
    assert stored.access_token == "session-access"
    assert stored.refresh_token == "session-refresh"


def test_missing_session_is_rejected() -> None:
    with pytest.raises(CredentialError, match="session response"):
        extract_session_from_har({"log": {"entries": []}})
