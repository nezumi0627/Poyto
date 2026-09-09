from __future__ import annotations

import importlib.util
import json
import sqlite3
from pathlib import Path

import pytest

SPEC = importlib.util.spec_from_file_location(
    "android_extract", Path(__file__).resolve().parents[1] / "scripts/extract_android_session.py"
)
assert SPEC and SPEC.loader
extract = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(extract)


def database(path: Path, *, duplicate: bool = False) -> bytes:
    db = sqlite3.connect(path)
    db.execute("CREATE TABLE catalystLocalStorage (key TEXT, value TEXT)")
    session = {"access_token": "token", "refresh_token": "refresh", "user": {"id": "uid"}}
    db.execute("INSERT INTO catalystLocalStorage VALUES (?, ?)", ("sb-test-auth-token", json.dumps(session)))
    db.execute("INSERT INTO catalystLocalStorage VALUES (?, ?)", ("unrelated", "private-account-data"))
    if duplicate:
        db.execute("INSERT INTO catalystLocalStorage VALUES (?, ?)", ("sb-other-auth-token", json.dumps(session)))
    db.commit()
    db.close()
    return path.read_bytes()


def test_extract_excludes_user_and_unrelated_data(tmp_path: Path) -> None:
    assert extract.extract_session(database(tmp_path / "db")) == {
        "access_token": "token", "refresh_token": "refresh",
    }


def test_extract_rejects_ambiguous_sessions(tmp_path: Path) -> None:
    with pytest.raises(extract.ExtractionError, match="unique"):
        extract.extract_session(database(tmp_path / "db", duplicate=True))


def test_save_private_and_never_overwrite(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("XDG_STATE_HOME", str(tmp_path))
    session = {"access_token": "token", "refresh_token": "refresh"}
    first = extract.save_session(session, None)
    second = extract.save_session(session, None)
    assert first != second
    for path in (first, second):
        assert path.stat().st_mode & 0o777 == 0o600
        assert json.loads(path.read_text()) == session
    with pytest.raises(extract.ExtractionError, match="already exists"):
        extract.save_session({}, first)
    with pytest.raises(extract.ExtractionError, match="outside"):
        extract.save_session({}, extract.REPOSITORY / "secret.json")


def test_device_selection(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(extract, "adb", lambda args: b"List of devices attached\na\tdevice\nb\toffline\n")
    assert extract.select_device("a") == "a"
    with pytest.raises(extract.ExtractionError):
        extract.select_device(None)
    with pytest.raises(extract.ExtractionError):
        extract.select_device("b")


def test_changed_database_is_rejected(monkeypatch: pytest.MonkeyPatch) -> None:
    responses = iter([b"0\n", b"", b"first", b"second", b""])
    monkeypatch.setattr(extract, "adb", lambda *args: next(responses))
    with pytest.raises(extract.ExtractionError, match="changed"):
        extract.read_database("device")


def test_adb_failure_does_not_print_captured_secrets(monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
    import subprocess

    monkeypatch.setattr(extract.subprocess, "run", lambda *args, **kwargs: subprocess.CompletedProcess(
        args=[], returncode=1, stdout=b"secret-access-token", stderr=b"secret-refresh-token",
    ))
    assert extract.main([]) == 1
    output = capsys.readouterr()
    assert "secret" not in output.out + output.err
