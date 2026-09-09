from __future__ import annotations

import os
import stat
import tempfile
from dataclasses import dataclass
from pathlib import Path

from .control_paths import ControlPathError, ControlPaths

_MAX_READ_TARGETS = 40
_MAX_DIR_ENTRIES = 200
_MAX_PATCH_BYTES = 1024 * 1024
_MAX_PATCH_SOURCE_BYTES = 16 * 1024 * 1024


def _has_glob(value: str) -> bool:
    return any(char in value for char in "*?[")


def _file_info(path: Path) -> str:
    info = path.stat()
    kind = "directory" if path.is_dir() else "file" if path.is_file() else "other"
    return f"{path} — {kind}, {info.st_size} B, mode {stat.filemode(info.st_mode)}"


class ControlReader:
    def __init__(self, paths: ControlPaths | None = None) -> None:
        self.paths = paths or ControlPaths.from_env()

    def _targets(self, values: list[str]) -> list[Path]:
        if not 1 <= len(values) <= 20:
            raise ValueError("paths must contain 1..20 entries")
        targets: list[Path] = []
        seen: set[Path] = set()
        for value in values:
            expanded = self.paths.glob(value, limit=20) if _has_glob(value) else [self.paths.resolve_existing(value)]
            for path in expanded:
                if path in seen:
                    continue
                seen.add(path)
                targets.append(path)
                if len(targets) > _MAX_READ_TARGETS:
                    raise ValueError(f"a read call may touch at most {_MAX_READ_TARGETS} targets")
        return targets

    @staticmethod
    def _directory(path: Path) -> str:
        entries = sorted(path.iterdir(), key=lambda item: item.name.lower())
        lines = [f"--- {path} — {len(entries)} entries, one level ---"]
        for entry in entries[:_MAX_DIR_ENTRIES]:
            suffix = "/" if entry.is_dir() else ""
            try:
                size = "" if entry.is_dir() else f"  {entry.stat().st_size} B"
            except OSError:
                size = "  <stat failed>"
            lines.append(f"{entry.name}{suffix}{size}")
        if len(entries) > _MAX_DIR_ENTRIES:
            lines.append(f"... stopped after {_MAX_DIR_ENTRIES} entries ...")
        return "\n".join(lines)

    @staticmethod
    def _text_file(path: Path, *, start_line: int | None, end_line: int | None, max_bytes: int) -> str:
        size = path.stat().st_size
        with path.open("rb") as handle:
            raw = handle.read(max_bytes + 1)
        truncated = len(raw) > max_bytes
        raw = raw[:max_bytes]
        if b"\0" in raw:
            return f"--- {_file_info(path)} ---\nBinary file; content not decoded."
        try:
            text = raw.decode("utf-8")
        except UnicodeDecodeError:
            return f"--- {_file_info(path)} ---\nNon-UTF-8 file; content not decoded."

        lines = text.splitlines()
        start = max(1, start_line or 1)
        end = min(len(lines), end_line or len(lines))
        if end < start:
            selected: list[str] = []
        else:
            selected = [f"{number}\t{lines[number - 1]}" for number in range(start, end + 1)]
        header = f"--- {path} — lines {start}-{end} of {len(lines)}, {size} B ---"
        if truncated:
            header += f"\n(read capped at {max_bytes} bytes; use a narrower line range or larger max_bytes)"
        return "\n".join([header, *selected])

    def read(
        self,
        paths: list[str],
        *,
        start_line: int | None = None,
        end_line: int | None = None,
        max_bytes: int = 256 * 1024,
    ) -> str:
        if start_line is not None and start_line < 1:
            raise ValueError("start_line must be >= 1")
        if end_line is not None and end_line < 1:
            raise ValueError("end_line must be >= 1")
        if not 1 <= max_bytes <= 512 * 1024:
            raise ValueError("max_bytes must be between 1 and 524288")
        rendered: list[str] = []
        for path in self._targets(paths):
            if path.is_dir():
                rendered.append(self._directory(path))
            elif path.is_file():
                rendered.append(
                    self._text_file(
                        path,
                        start_line=start_line,
                        end_line=end_line,
                        max_bytes=max_bytes,
                    )
                )
            else:
                rendered.append(f"--- {_file_info(path)} ---")
        if not rendered:
            return "No matching files."
        return "\n\n".join(rendered)


@dataclass(slots=True)
class _PatchAction:
    kind: str
    path: str
    lines: list[str]
    move_to: str | None = None


def _patch_lines(patch: str) -> list[str]:
    if len(patch.encode("utf-8")) > _MAX_PATCH_BYTES:
        raise ValueError("patch exceeds the 1 MiB input limit")
    lines = patch.strip().splitlines()
    if lines and lines[0] in {"<<EOF", "<<'EOF'", '<<"EOF"'} and lines[-1].endswith("EOF"):
        lines = lines[1:-1]
    if not lines or lines[0].strip() != "*** Begin Patch" or lines[-1].strip() != "*** End Patch":
        raise ValueError("patch must start with '*** Begin Patch' and end with '*** End Patch'")
    return lines[1:-1]


def _parse_patch(patch: str) -> list[_PatchAction]:
    lines = _patch_lines(patch)
    actions: list[_PatchAction] = []
    index = 0
    while index < len(lines):
        marker = lines[index]
        if marker.startswith("*** Add File: "):
            kind, path = "add", marker.removeprefix("*** Add File: ")
        elif marker.startswith("*** Delete File: "):
            actions.append(_PatchAction("delete", marker.removeprefix("*** Delete File: "), []))
            index += 1
            continue
        elif marker.startswith("*** Update File: "):
            kind, path = "update", marker.removeprefix("*** Update File: ")
        else:
            raise ValueError(f"invalid patch marker: {marker}")
        if not path.strip():
            raise ValueError("patch file path must not be empty")

        index += 1
        move_to: str | None = None
        if kind == "update" and index < len(lines) and lines[index].startswith("*** Move to: "):
            move_to = lines[index].removeprefix("*** Move to: ")
            index += 1
        body: list[str] = []
        while index < len(lines) and not lines[index].startswith(
            ("*** Add File: ", "*** Delete File: ", "*** Update File: ")
        ):
            body.append(lines[index])
            index += 1
        actions.append(_PatchAction(kind, path, body, move_to))
    if not actions:
        raise ValueError("patch contains no file actions")
    return actions


def _find_sequence(haystack: list[str], needle: list[str], start: int) -> int:
    if not needle:
        return start
    limit = len(haystack) - len(needle) + 1
    for index in range(max(0, start), max(0, limit)):
        if haystack[index : index + len(needle)] == needle:
            return index
    return -1


def _apply_update(original: str, body: list[str]) -> str:
    old_lines = original.splitlines()
    final_newline = original.endswith("\n")
    cursor = 0
    index = 0
    while index < len(body):
        if body[index] == "*** End of File":
            index += 1
            continue
        hint: str | None = None
        if body[index].startswith("@@"):
            hint = body[index][2:].strip() or None
            index += 1
        chunk: list[str] = []
        while index < len(body) and not body[index].startswith("@@") and body[index] != "*** End of File":
            chunk.append(body[index])
            index += 1
        if not chunk:
            continue
        if any(not line.startswith((" ", "+", "-")) for line in chunk):
            raise ValueError("update hunk lines must begin with space, +, or -")
        before = [line[1:] for line in chunk if line.startswith((" ", "-"))]
        after = [line[1:] for line in chunk if line.startswith((" ", "+"))]
        search_start = cursor
        if hint:
            hint_pos = _find_sequence(old_lines, [hint], cursor)
            if hint_pos >= 0:
                search_start = hint_pos
        position = _find_sequence(old_lines, before, search_start)
        if position < 0:
            preview = "\\n".join(before[:5])
            raise ValueError(f"update context was not found in target file near: {preview!r}")
        old_lines[position : position + len(before)] = after
        cursor = position + len(after)
    rendered = "\n".join(old_lines)
    if final_newline and (rendered or original):
        rendered += "\n"
    return rendered


class ControlPatcher:
    def __init__(self, paths: ControlPaths | None = None) -> None:
        self.paths = paths or ControlPaths.from_env()

    def apply_patch(self, patch: str, *, workdir: str | None = None) -> str:
        base = self.paths.resolve_existing(workdir or self.paths.default_workdir())
        if not base.is_dir():
            raise ControlPathError(f"workdir is not a directory: {base}")
        actions = _parse_patch(patch)
        planned: list[tuple[_PatchAction, Path, Path | None, str | None]] = []

        for action in actions:
            target = self.paths.resolve_target(action.path, base=base)
            move_target = self.paths.resolve_target(action.move_to, base=base) if action.move_to else None
            content: str | None = None
            if action.kind == "add":
                if target.exists():
                    raise ValueError(f"cannot add existing path: {action.path}")
                if not action.lines or any(not line.startswith("+") for line in action.lines):
                    raise ValueError(f"add file lines must all begin with +: {action.path}")
                content = "\n".join(line[1:] for line in action.lines) + "\n"
            elif action.kind == "delete":
                existing = self.paths.resolve_existing(target)
                if not existing.is_file():
                    raise ValueError(f"delete target is not a regular file: {action.path}")
            elif action.kind == "update":
                existing = self.paths.resolve_existing(target)
                if not existing.is_file():
                    raise ValueError(f"update target is not a regular file: {action.path}")
                if existing.stat().st_size > _MAX_PATCH_SOURCE_BYTES:
                    raise ValueError(f"file exceeds {_MAX_PATCH_SOURCE_BYTES} byte patch limit: {action.path}")
                original = existing.read_text(encoding="utf-8")
                content = _apply_update(original, action.lines)
                if move_target and move_target.exists() and move_target.resolve() != existing.resolve():
                    raise ValueError(f"move destination already exists: {action.move_to}")
            planned.append((action, target, move_target, content))

        temp_files: list[tuple[Path, Path]] = []
        try:
            for action, target, move_target, content in planned:
                if action.kind not in {"add", "update"}:
                    continue
                destination = move_target or target
                destination.parent.mkdir(parents=True, exist_ok=True)
                fd, temp_name = tempfile.mkstemp(prefix=".poyto-patch-", dir=destination.parent)
                os.close(fd)
                temp = Path(temp_name)
                temp.write_text(content or "", encoding="utf-8")
                temp_files.append((temp, destination))

            for temp, destination in temp_files:
                os.replace(temp, destination)
            for action, target, move_target, _ in planned:
                if action.kind == "delete":
                    target.unlink()
                elif action.kind == "update" and move_target and target != move_target:
                    target.unlink()
        finally:
            for temp, _ in temp_files:
                try:
                    temp.unlink()
                except FileNotFoundError:
                    pass

        added = [action.path for action, _, _, _ in planned if action.kind == "add"]
        updated = [
            action.move_to or action.path for action, _, _, _ in planned if action.kind == "update"
        ]
        deleted = [action.path for action, _, _, _ in planned if action.kind == "delete"]
        parts: list[str] = []
        if added:
            parts.append("Added: " + ", ".join(added))
        if updated:
            parts.append("Updated: " + ", ".join(updated))
        if deleted:
            parts.append("Deleted: " + ", ".join(deleted))
        return "\n".join(parts)


__all__ = ["ControlPatcher", "ControlReader"]
