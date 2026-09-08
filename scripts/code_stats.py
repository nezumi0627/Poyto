from __future__ import annotations

from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src" / "poyto"
TESTS = ROOT / "tests"


def count_lines(path: Path) -> tuple[int, int]:
    lines = path.read_text(encoding="utf-8").splitlines()
    nonblank = sum(1 for line in lines if line.strip())
    return len(lines), nonblank


def main() -> None:
    files = sorted(SRC.rglob("*.py"))
    groups: dict[str, list[Path]] = defaultdict(list)
    for path in files:
        rel = path.relative_to(SRC)
        group = "resources" if rel.parts[0] == "resources" else "core"
        groups[group].append(path)

    print("Poyto source LOC snapshot")
    total_lines = 0
    total_nonblank = 0
    for group in ("core", "resources"):
        group_lines = 0
        group_nonblank = 0
        for path in groups[group]:
            lines, nonblank = count_lines(path)
            group_lines += lines
            group_nonblank += nonblank
        total_lines += group_lines
        total_nonblank += group_nonblank
        print(f"{group}: files={len(groups[group])} lines={group_lines} nonblank={group_nonblank}")

    test_files = sorted(TESTS.rglob("test_*.py"))
    test_lines = sum(count_lines(path)[0] for path in test_files)
    test_nonblank = sum(count_lines(path)[1] for path in test_files)
    print(f"tests: files={len(test_files)} lines={test_lines} nonblank={test_nonblank}")
    print(f"source-total: files={len(files)} lines={total_lines} nonblank={total_nonblank}")

    print("\nPer source file:")
    for path in files:
        lines, nonblank = count_lines(path)
        print(f"{path.relative_to(ROOT)}: lines={lines} nonblank={nonblank}")


if __name__ == "__main__":
    main()
