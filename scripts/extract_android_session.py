#!/usr/bin/env python3
"""Extract an existing POYP session from an authorized rooted Android device."""
from __future__ import annotations

import argparse
import json
import os
import shlex
import sqlite3
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

DATABASE = "/data/user/0/com.poyp.poyp/databases/RKStorage"
REPOSITORY = Path(__file__).resolve().parents[1]


class ExtractionError(Exception):
    """An actionable error that contains no captured data."""


def adb(args: list[str], serial: str | None = None) -> bytes:
    if args[0] in {"shell", "exec-out"}:
        args = [args[0], shlex.join(args[1:])]
    command = ["adb"] + (["-s", serial] if serial else []) + args
    try:
        result = subprocess.run(command, capture_output=True, timeout=30, check=False)
    except FileNotFoundError as exc:
        raise ExtractionError("adb is not installed or not on PATH.") from exc
    except subprocess.TimeoutExpired as exc:
        raise ExtractionError("ADB timed out. Check the device and its su permission prompt.") from exc
    if result.returncode:
        raise ExtractionError("ADB command failed. Check the connection, su permission and POYP installation.")
    return result.stdout


def select_device(serial: str | None) -> str:
    devices = {}
    for line in adb(["devices"]).decode("utf-8", errors="replace").splitlines():
        parts = line.split()
        if len(parts) == 2 and parts[0] != "List":
            devices[parts[0]] = parts[1]
    if serial:
        if devices.get(serial) != "device":
            raise ExtractionError("The selected device is missing, offline or unauthorized.")
        return serial
    if len(devices) != 1:
        raise ExtractionError("Connect exactly one device, or select one with --serial (see adb devices).")
    selected, status = next(iter(devices.items()))
    if status != "device":
        raise ExtractionError("The device is offline or unauthorized. Approve USB debugging on Android.")
    return selected


def read_database(serial: str) -> bytes:
    uid = adb(["shell", "su", "-c", "id -u"], serial).strip()
    if uid != b"0":
        raise ExtractionError("su did not grant root. Approve root access on Android and retry.")
    # Reject a database with pending journal/WAL bytes rather than silently
    # exporting an old main-file snapshot without its sidecars.
    check = f"test ! -s {DATABASE}-wal && test ! -s {DATABASE}-journal"
    try:
        adb(["shell", "su", "-c", check], serial)
    except ExtractionError as exc:
        raise ExtractionError("Cannot confirm idle storage (journal/WAL). Leave POYP idle and retry.") from exc
    data = adb(["exec-out", "su", "-c", f"cat {DATABASE}"], serial)
    second = adb(["exec-out", "su", "-c", f"cat {DATABASE}"], serial)
    try:
        adb(["shell", "su", "-c", check], serial)
    except ExtractionError as exc:
        raise ExtractionError("Storage changed or ADB failed. Leave POYP idle and retry.") from exc
    if data != second:
        raise ExtractionError("POYP storage changed while reading. Leave the app idle and retry.")
    if not data.startswith(b"SQLite format 3\x00"):
        raise ExtractionError("Expected a SQLite database. This POYP storage version is unsupported.")
    return data


def extract_session(data: bytes) -> dict[str, Any]:
    # A private temporary directory supports Python 3.10 too. The raw database
    # never enters the repository and is removed when this context exits.
    with tempfile.TemporaryDirectory(prefix="poyto-android-", dir="/tmp") as directory:
        path = Path(directory) / "storage.sqlite"
        fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        with os.fdopen(fd, "wb") as output:
            output.write(data)
        db = sqlite3.connect(f"{path.as_uri()}?mode=ro&immutable=1", uri=True)
        try:
            if db.execute("PRAGMA quick_check").fetchone() != ("ok",):
                raise ExtractionError("Database copy is inconsistent. Leave the app idle and retry.")
            rows = db.execute("SELECT key, value FROM catalystLocalStorage")
            sessions = []
            for key, value in rows:
                if not isinstance(key, str) or not (key.startswith("sb-") and key.endswith("-auth-token")):
                    continue
                try:
                    session = json.loads(value)
                except (ValueError, TypeError):
                    continue
                if isinstance(session, dict) and all(
                    isinstance(session.get(field), str) and session[field].strip()
                    for field in ("access_token", "refresh_token")
                ):
                    sessions.append(session)
        except sqlite3.Error as exc:
            raise ExtractionError("Cannot read the observed POYP storage schema. Check the app version.") from exc
        finally:
            db.close()
    if len(sessions) != 1:
        raise ExtractionError("No unique access/refresh token pair found. Check that POYP is logged in.")
    fields = ("access_token", "refresh_token", "token_type", "expires_in", "expires_at")
    return {key: sessions[0][key] for key in fields if key in sessions[0]}


def save_session(session: dict[str, Any], requested: Path | None) -> Path:
    state = Path(os.getenv("XDG_STATE_HOME") or Path.home() / ".local/state")
    target = (requested or state / "poyto/android-session.json").expanduser().absolute()
    if target.resolve().is_relative_to(REPOSITORY):
        raise ExtractionError("Save credentials outside the Poyto repository.")
    target.parent.mkdir(parents=True, exist_ok=True)
    try:
        fd = os.open(target, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    except FileExistsError as exc:
        if requested:
            raise ExtractionError("Output already exists; choose a new --output path.") from exc
        fd, name = tempfile.mkstemp(prefix="android-session-", suffix=".json", dir=target.parent)
        target = Path(name)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as output:
            json.dump(session, output, indent=2)
            output.write("\n")
    except BaseException:
        target.unlink(missing_ok=True)
        raise
    return target


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--serial", default=os.getenv("ANDROID_SERIAL"), help="ADB device serial")
    parser.add_argument("--output", type=Path, help="New output JSON path outside the repository")
    args = parser.parse_args(argv)
    try:
        serial = select_device(args.serial)
        target = save_session(extract_session(read_database(serial)), args.output)
    except ExtractionError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1
    except OSError:
        print("Error: Cannot create/read the private local files. Check permissions and free space.", file=sys.stderr)
        return 1
    print(f"Saved private session file: {target}")
    print("Credentials were not printed. Server validity has not been checked.")
    print("Import using your Poyto installation:")
    print(f"  poyto login {shlex.quote('@' + str(target))}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
