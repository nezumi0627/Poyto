from __future__ import annotations

import os
import pty
import secrets
import shlex
import shutil
import signal
import subprocess
import threading
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from .control_paths import ControlPathError, ControlPaths

_MAX_BUFFER_BYTES = 1024 * 1024
_MAX_SESSIONS = 16
_DEFAULT_YIELD_MS = 10_000
_DEFAULT_STDIN_YIELD_MS = 5_000
_MAX_YIELD_MS = 30_000
_SESSION_TTL_SECONDS = 60 * 60


def _approx_tokens(text: str) -> int:
    return (len(text.encode("utf-8", errors="replace")) + 3) // 4


def _truncate(text: str, max_tokens: int) -> str:
    budget = max(1, min(max_tokens, 250_000)) * 4
    raw = text.encode("utf-8", errors="replace")
    if len(raw) <= budget:
        return text
    head = budget // 2
    tail = budget - head
    omitted = len(raw) - budget
    result = raw[:head] + f"\n... {omitted} bytes omitted ...\n".encode() + raw[-tail:]
    return result.decode("utf-8", errors="replace")


def _child_environment() -> dict[str, str]:
    env = dict(os.environ)
    # The command bridge itself is already a high-authority capability, but connector
    # credentials should not be handed to every child process for free.
    sensitive = {
        "POYTO_PLUGIN_TOKEN",
        "OPENAI_API_KEY",
        "OPENAI_TUNNEL_API_KEY",
        "CLOUDFLARE_API_TOKEN",
        "CLOUDFLARE_API_KEY",
        "POYTO_TOKEN",
        "POYTO_ACCESS_TOKEN",
        "POYTO_REFRESH_TOKEN",
        "POYTO_APPLE_ID_TOKEN",
        "POYTO_APPLE_ACCESS_TOKEN",
    }
    for key in sensitive:
        env.pop(key, None)
    env.update(
        {
            "TERM": env.get("TERM", "xterm-256color"),
            "PAGER": "cat",
            "GIT_PAGER": "cat",
            "SYSTEMD_PAGER": "cat",
            "NO_COLOR": env.get("NO_COLOR", "1"),
        }
    )
    return env


def _batch_script(commands: list[str]) -> str:
    lines = ["__poyto_first_exit=0"]
    count = len(commands)
    for index, command in enumerate(commands, 1):
        marker = f"--- command {index}/{count} ---"
        lines.extend(
            [
                f"printf '%s\\n' {shlex.quote(marker)}",
                command,
                "__poyto_ec=$?",
                "if [ \"$__poyto_first_exit\" -eq 0 ] && [ \"$__poyto_ec\" -ne 0 ]; then __poyto_first_exit=$__poyto_ec; fi",
                f"printf '%s %s\\n' {shlex.quote('--- exit code')} \"$__poyto_ec ---\"",
            ]
        )
    lines.append("exit \"$__poyto_first_exit\"")
    return "\n".join(lines)


@dataclass(slots=True)
class _ProcessSession:
    process: subprocess.Popen[bytes]
    tty: bool
    master_fd: int | None
    started_at: float = field(default_factory=time.monotonic)
    touched_at: float = field(default_factory=time.monotonic)
    buffer: bytearray = field(default_factory=bytearray)
    dropped_bytes: int = 0
    lock: threading.Lock = field(default_factory=threading.Lock)
    output_event: threading.Event = field(default_factory=threading.Event)
    reader_done: threading.Event = field(default_factory=threading.Event)

    def start_reader(self) -> None:
        thread = threading.Thread(target=self._reader, name=f"poyto-exec-{self.process.pid}", daemon=True)
        thread.start()

    def _reader(self) -> None:
        try:
            if self.tty:
                assert self.master_fd is not None
                while True:
                    try:
                        chunk = os.read(self.master_fd, 8192)
                    except OSError:
                        break
                    if not chunk:
                        break
                    self._append(chunk)
            else:
                assert self.process.stdout is not None
                while True:
                    chunk = self.process.stdout.read(8192)
                    if not chunk:
                        break
                    self._append(chunk)
        finally:
            self.reader_done.set()
            self.output_event.set()

    def _append(self, chunk: bytes) -> None:
        with self.lock:
            self.buffer.extend(chunk)
            if len(self.buffer) > _MAX_BUFFER_BYTES:
                overflow = len(self.buffer) - _MAX_BUFFER_BYTES
                del self.buffer[:overflow]
                self.dropped_bytes += overflow
        self.output_event.set()

    def drain(self) -> bytes:
        with self.lock:
            data = bytes(self.buffer)
            self.buffer.clear()
            dropped = self.dropped_bytes
            self.dropped_bytes = 0
            self.output_event.clear()
        if dropped:
            return f"... {dropped} earlier bytes omitted ...\n".encode() + data
        return data

    def write(self, chars: str) -> None:
        payload = chars.encode()
        if self.tty:
            if self.master_fd is None:
                raise RuntimeError("terminal input is closed")
            os.write(self.master_fd, payload)
        else:
            if self.process.stdin is None or self.process.stdin.closed:
                raise RuntimeError("stdin is closed; rerun exec_command with tty=true if interactive input is needed")
            self.process.stdin.write(payload)
            self.process.stdin.flush()
        self.touched_at = time.monotonic()

    def close(self) -> None:
        if self.process.poll() is None:
            try:
                os.killpg(self.process.pid, signal.SIGTERM)
            except (ProcessLookupError, PermissionError):
                self.process.terminate()
        if self.master_fd is not None:
            try:
                os.close(self.master_fd)
            except OSError:
                pass


class ExecManager:
    def __init__(self, paths: ControlPaths | None = None) -> None:
        self.paths = paths or ControlPaths.from_env()
        self._sessions: dict[int, _ProcessSession] = {}
        self._lock = threading.Lock()

    def _cleanup(self) -> None:
        now = time.monotonic()
        with self._lock:
            stale = [
                session_id
                for session_id, session in self._sessions.items()
                if now - session.touched_at > _SESSION_TTL_SECONDS
            ]
            for session_id in stale:
                session = self._sessions.pop(session_id)
                session.close()

    @staticmethod
    def _shell(value: str | None) -> str:
        shell = value or ("/bin/bash" if Path("/bin/bash").exists() else "/bin/sh")
        if not shell.startswith("/") or "\n" in shell or "\r" in shell:
            raise ValueError("shell must be an absolute executable path")
        return shell

    def _spawn_argv(self, script: str, shell: str, workdir: Path) -> tuple[list[str], str]:
        if self.paths.exec_mode == "container":
            if not Path(shell).is_file():
                raise ValueError(f"shell does not exist in the container: {shell}")
            return [shell, "-lc", script], str(workdir)

        if os.geteuid() != 0:
            raise PermissionError("host exec mode requires the plugin container to run as root")
        nsenter = shutil.which("nsenter")
        if not nsenter or not Path("/proc/1/ns/mnt").exists():
            raise RuntimeError("host exec mode requires nsenter and Docker pid: host")
        host_workdir = self.paths.host_workdir(workdir)
        command = f"cd -- {shlex.quote(host_workdir)} && exec {shlex.quote(shell)} -lc {shlex.quote(script)}"
        argv = [
            nsenter,
            "--target",
            "1",
            "--mount",
            "--uts",
            "--ipc",
            "--net",
            "--pid",
            "--",
            "/usr/bin/env",
            "-i",
            "HOME=/root",
            "USER=root",
            "LOGNAME=root",
            "PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin",
            "/bin/sh",
            "-lc",
            command,
        ]
        return argv, "/"

    def _start(self, script: str, *, shell: str, workdir: Path, tty: bool) -> _ProcessSession:
        argv, cwd = self._spawn_argv(script, shell, workdir)
        if tty:
            master_fd, slave_fd = pty.openpty()
            try:
                process = subprocess.Popen(
                    argv,
                    cwd=cwd,
                    env=_child_environment(),
                    stdin=slave_fd,
                    stdout=slave_fd,
                    stderr=slave_fd,
                    start_new_session=True,
                )
            finally:
                os.close(slave_fd)
            session = _ProcessSession(process=process, tty=True, master_fd=master_fd)
        else:
            process = subprocess.Popen(
                argv,
                cwd=cwd,
                env=_child_environment(),
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                start_new_session=True,
            )
            session = _ProcessSession(process=process, tty=False, master_fd=None)
        session.start_reader()
        return session

    @staticmethod
    def _wait(session: _ProcessSession, yield_time_ms: int) -> None:
        deadline = time.monotonic() + max(0, min(yield_time_ms, _MAX_YIELD_MS)) / 1000
        while time.monotonic() < deadline:
            if session.process.poll() is not None:
                session.reader_done.wait(0.15)
                return
            remaining = max(0.0, deadline - time.monotonic())
            session.output_event.wait(min(0.1, remaining))
            # Keep waiting until the requested yield deadline; this matches the useful
            # property of Codex unified exec that a noisy long-running process still gets
            # a stable background session instead of returning one byte per call.

    @staticmethod
    def _output(
        session: _ProcessSession,
        *,
        session_id: int | None,
        max_output_tokens: int,
    ) -> dict[str, Any]:
        text = session.drain().decode("utf-8", errors="replace")
        original_tokens = _approx_tokens(text)
        result: dict[str, Any] = {
            "chunk_id": secrets.token_hex(3),
            "wall_time_seconds": round(time.monotonic() - session.started_at, 6),
            "original_token_count": original_tokens,
            "output": _truncate(text, max_output_tokens),
        }
        code = session.process.poll()
        if code is not None:
            result["exit_code"] = code
        elif session_id is not None:
            result["session_id"] = session_id
        return result

    def exec_command(
        self,
        *,
        cmd: str | None = None,
        cmds: list[str] | None = None,
        workdir: str | None = None,
        tty: bool = False,
        yield_time_ms: int = _DEFAULT_YIELD_MS,
        max_output_tokens: int = 10_000,
        shell: str | None = None,
    ) -> dict[str, Any]:
        self._cleanup()
        if (cmd is None) == (cmds is None):
            raise ValueError("provide exactly one of cmd or cmds")
        if cmd is not None:
            if not cmd.strip():
                raise ValueError("cmd must not be empty")
            script = cmd
        else:
            assert cmds is not None
            if not 1 <= len(cmds) <= 20 or any(not item.strip() for item in cmds):
                raise ValueError("cmds must contain 1..20 non-empty commands")
            script = _batch_script(cmds)

        resolved_workdir = self.paths.resolve_existing(workdir or self.paths.default_workdir())
        if not resolved_workdir.is_dir():
            raise ControlPathError(f"workdir is not a directory: {resolved_workdir}")
        session = self._start(script, shell=self._shell(shell), workdir=resolved_workdir, tty=tty)
        self._wait(session, yield_time_ms)
        if session.process.poll() is not None:
            result = self._output(session, session_id=None, max_output_tokens=max_output_tokens)
            session.close()
            return result

        with self._lock:
            if len(self._sessions) >= _MAX_SESSIONS:
                session.close()
                raise RuntimeError(f"at most {_MAX_SESSIONS} background command sessions may run")
            while True:
                session_id = secrets.randbelow(2_000_000_000) + 1
                if session_id not in self._sessions:
                    break
            self._sessions[session_id] = session
        return self._output(session, session_id=session_id, max_output_tokens=max_output_tokens)

    def write_stdin(
        self,
        *,
        session_id: int,
        chars: str = "",
        yield_time_ms: int = _DEFAULT_STDIN_YIELD_MS,
        max_output_tokens: int = 10_000,
    ) -> dict[str, Any]:
        self._cleanup()
        with self._lock:
            session = self._sessions.get(session_id)
        if session is None:
            raise KeyError(f"unknown command session id {session_id}")
        if chars:
            session.write(chars)
        session.touched_at = time.monotonic()
        self._wait(session, yield_time_ms)
        result = self._output(session, session_id=session_id, max_output_tokens=max_output_tokens)
        if session.process.poll() is not None:
            with self._lock:
                self._sessions.pop(session_id, None)
            session.close()
        return result

    def close(self) -> None:
        with self._lock:
            sessions = list(self._sessions.values())
            self._sessions.clear()
        for session in sessions:
            session.close()


__all__ = ["ExecManager"]
