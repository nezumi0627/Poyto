from __future__ import annotations

import glob
import os
from dataclasses import dataclass
from pathlib import Path


class ControlPathError(ValueError):
    pass


def _inside(root: Path, path: Path) -> bool:
    try:
        return os.path.commonpath((str(root), str(path))) == str(root)
    except ValueError:
        return False


@dataclass(frozen=True, slots=True)
class ControlPaths:
    roots: tuple[Path, ...]
    host_root: Path
    exec_mode: str

    @classmethod
    def from_env(cls) -> ControlPaths:
        raw = os.getenv("POYTO_PLUGIN_ROOTS", "/workspace:/data")
        roots: list[Path] = []
        for item in raw.split(os.pathsep):
            if not item.strip():
                continue
            path = Path(item).expanduser().resolve(strict=False)
            if path not in roots:
                roots.append(path)
        if not roots:
            raise ControlPathError("POYTO_PLUGIN_ROOTS must contain at least one path")

        mode = os.getenv("POYTO_PLUGIN_EXEC_MODE", "container").strip().lower()
        if mode not in {"container", "host"}:
            raise ControlPathError("POYTO_PLUGIN_EXEC_MODE must be 'container' or 'host'")
        return cls(
            roots=tuple(roots),
            host_root=Path(os.getenv("POYTO_PLUGIN_HOST_ROOT", "/host")).resolve(strict=False),
            exec_mode=mode,
        )

    def describe_roots(self) -> str:
        return ", ".join(str(root) for root in self.roots)

    def default_workdir(self) -> Path:
        for root in self.roots:
            if root.is_dir():
                return root
        return self.roots[0]

    def _candidate(self, value: str | Path, *, base: Path | None = None) -> Path:
        path = Path(value).expanduser()
        if not path.is_absolute():
            path = (base or self.default_workdir()) / path
        return path

    def _authorize(self, path: Path) -> Path:
        resolved = path.resolve(strict=False)
        if not any(_inside(root, resolved) for root in self.roots):
            raise ControlPathError(
                f"path is outside approved plugin roots ({self.describe_roots()}): {path}"
            )
        return resolved

    def resolve_existing(self, value: str | Path, *, base: Path | None = None) -> Path:
        candidate = self._candidate(value, base=base)
        resolved = candidate.resolve(strict=True)
        return self._authorize(resolved)

    def resolve_target(self, value: str | Path, *, base: Path | None = None) -> Path:
        candidate = self._candidate(value, base=base)
        # Resolve the deepest existing ancestor. This rejects a missing target reached
        # through a symlink that escapes an approved root.
        probe = candidate
        missing: list[str] = []
        while not probe.exists() and probe != probe.parent:
            missing.append(probe.name)
            probe = probe.parent
        ancestor = probe.resolve(strict=True)
        if not any(_inside(root, ancestor) for root in self.roots):
            raise ControlPathError(
                f"path is outside approved plugin roots ({self.describe_roots()}): {candidate}"
            )
        resolved = ancestor.joinpath(*reversed(missing))
        return self._authorize(resolved)

    def glob(self, pattern: str, *, limit: int = 20) -> list[Path]:
        candidate = self._candidate(pattern)
        # The literal prefix is authorization-checked before glob expansion, and each
        # result is checked again after symlink resolution.
        prefix_parts: list[str] = []
        for part in candidate.parts:
            if any(ch in part for ch in "*?["):
                break
            prefix_parts.append(part)
        prefix = Path(*prefix_parts) if prefix_parts else candidate.parent
        self.resolve_target(prefix)
        matches: list[Path] = []
        for value in glob.iglob(str(candidate), recursive=True):
            try:
                resolved = self.resolve_existing(value)
            except (FileNotFoundError, ControlPathError):
                continue
            matches.append(resolved)
            if len(matches) >= limit:
                break
        return matches

    def host_workdir(self, container_workdir: Path) -> str:
        if self.exec_mode != "host":
            return str(container_workdir)
        resolved = self.resolve_existing(container_workdir)
        if not _inside(self.host_root, resolved):
            raise ControlPathError(
                f"host exec workdir must be beneath {self.host_root}; got {resolved}"
            )
        relative = resolved.relative_to(self.host_root)
        return "/" + relative.as_posix() if relative.parts else "/"


__all__ = ["ControlPathError", "ControlPaths"]
