from poyto import AuthSession, session_info, token_kind


def test_token_kind_distinguishes_jwt_and_opaque():
    assert token_kind("header.payload.signature") == "jwt"
    assert token_kind("opaque-refresh-token") == "opaque"
    assert token_kind(None) is None


def test_session_info_never_exposes_token_values():
    session = AuthSession(
        access_token="header.payload.signature",
        refresh_token="opaque-refresh-token",
        expires_in=3600,
        expires_at=1234567890,
        user={"id": "user-id"},
    )
    info = session_info(session).to_dict()

    assert info == {
        "authenticated": True,
        "access_token_kind": "jwt",
        "has_refresh_token": True,
        "refresh_token_kind": "opaque",
        "expires_in": 3600,
        "expires_at": 1234567890,
        "user_id": "user-id",
    }
    assert "header.payload.signature" not in repr(info)
    assert "opaque-refresh-token" not in repr(info)


def test_session_info_without_session():
    assert session_info(None).to_dict() == {
        "authenticated": False,
        "access_token_kind": None,
        "has_refresh_token": False,
        "refresh_token_kind": None,
        "expires_in": None,
        "expires_at": None,
        "user_id": None,
    }
