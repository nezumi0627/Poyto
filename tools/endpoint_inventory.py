from __future__ import annotations

import argparse
import csv
import io
import json
import re
import sys
import zipfile
from collections.abc import Sequence
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any
from urllib.parse import parse_qsl, urlsplit

POYP_HOST_SUFFIX = "poyp.app"
UUID_RE = re.compile(
    r"(?i)\b[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}\b"
)
LONG_NUMERIC_SEGMENT_RE = re.compile(r"(?<=/)[0-9]{12,}(?=/|$)")
URL_RE = re.compile(rb"https?://[^\x00-\x20\x7f\"'<>]{4,}")
API_PATH_RE = re.compile(rb"/(?:api|auth/v1)/[a-z0-9][A-Za-z0-9_./?&={}:$%+\-]*")
PRINTABLE_RE = re.compile(rb"[\x20-\x7e]{6,}")
DOC_ROUTE_RE = re.compile(
    r"`(?:(GET|POST|PUT|DELETE|PATCH|HEAD|OPTIONS)\s+)?(/(?:api|auth/v1)/[^`?\s]+)(?:\?[^`]*)?`"
)
DECOMPILED_METHOD_RE = re.compile(
    r"^\s*(r\d+) = '(GET|POST|PUT|DELETE|PATCH|HEAD|OPTIONS)';\s*$"
)
DECOMPILED_METHOD_PROP_RE = re.compile(r"^\s*(r\d+)\['method'\] = (r\d+);\s*$")
DECOMPILED_ROUTE_RE = re.compile(r"^\s*(r\d+) = '(/[^'\r\n]+)';\s*$")

SCAN_SUFFIXES = {
    ".bundle",
    ".dex",
    ".js",
    ".json",
    ".map",
    ".so",
    ".txt",
    ".xml",
}
MAX_MEMBER_SIZE = 128 * 1024 * 1024


@dataclass
class Endpoint:
    host: str
    path: str
    method: str | None = None
    query_keys: set[str] = field(default_factory=set)
    body_keys: set[str] = field(default_factory=set)
    statuses: set[int] = field(default_factory=set)
    sources: set[str] = field(default_factory=set)
    evidence: set[str] = field(default_factory=set)
    occurrences: int = 0

    def key(self) -> tuple[str, str, str]:
        return (self.host, self.method or "", self.path)

    def as_dict(self) -> dict[str, Any]:
        confidence = "observed" if "observed" in self.evidence else "static"
        return {
            "method": self.method,
            "host": self.host,
            "path": self.path,
            "query_keys": sorted(self.query_keys),
            "body_keys": sorted(self.body_keys),
            "statuses": sorted(self.statuses),
            "source": sorted(self.sources),
            "confidence": confidence,
            "occurrences": self.occurrences,
        }


def normalize_path(path: str) -> str:
    path = UUID_RE.sub("{uuid}", path)
    path = LONG_NUMERIC_SEGMENT_RE.sub("{id}", path)
    return path.rstrip("/\"'`,;)]}") or "/"


def is_poyp_host(host: str) -> bool:
    host = host.lower().rstrip(".")
    return host == POYP_HOST_SUFFIX or host.endswith("." + POYP_HOST_SUFFIX)


def body_keys(request: dict[str, Any]) -> set[str]:
    post_data = request.get("postData")
    if not isinstance(post_data, dict):
        return set()

    text = post_data.get("text")
    if isinstance(text, str) and text.strip():
        try:
            parsed = json.loads(text)
        except json.JSONDecodeError:
            parsed = None
        if isinstance(parsed, dict):
            return {str(key) for key in parsed}

    params = post_data.get("params")
    if isinstance(params, list):
        return {
            str(item["name"])
            for item in params
            if isinstance(item, dict) and isinstance(item.get("name"), str)
        }
    return set()


def merge_endpoint(target: dict[tuple[str, str, str], Endpoint], endpoint: Endpoint) -> None:
    key = endpoint.key()
    existing = target.get(key)
    if existing is None:
        target[key] = endpoint
        return
    existing.query_keys.update(endpoint.query_keys)
    existing.body_keys.update(endpoint.body_keys)
    existing.statuses.update(endpoint.statuses)
    existing.sources.update(endpoint.sources)
    existing.evidence.update(endpoint.evidence)
    existing.occurrences += endpoint.occurrences


def add_har_document(
    inventory: dict[tuple[str, str, str], Endpoint],
    document: dict[str, Any],
    source: str,
    *,
    all_hosts: bool,
) -> None:
    log = document.get("log")
    entries = log.get("entries") if isinstance(log, dict) else None
    if not isinstance(entries, list):
        return

    for entry in entries:
        if not isinstance(entry, dict):
            continue
        request = entry.get("request")
        response = entry.get("response")
        if not isinstance(request, dict):
            continue

        raw_url = request.get("url")
        if not isinstance(raw_url, str):
            continue
        parts = urlsplit(raw_url)
        host = (parts.hostname or "").lower()
        if not host or (not all_hosts and not is_poyp_host(host)):
            continue

        method = request.get("method")
        method = method.upper() if isinstance(method, str) else None
        status = response.get("status") if isinstance(response, dict) else None
        query_keys = {name for name, _ in parse_qsl(parts.query, keep_blank_values=True)}
        endpoint = Endpoint(
            host=host,
            method=method,
            path=normalize_path(parts.path),
            query_keys=query_keys,
            body_keys=body_keys(request),
            statuses={status} if isinstance(status, int) and status > 0 else set(),
            sources={source},
            evidence={"observed"},
            occurrences=1,
        )
        merge_endpoint(inventory, endpoint)


def load_har_bytes(
    inventory: dict[tuple[str, str, str], Endpoint],
    data: bytes,
    source: str,
    *,
    all_hosts: bool,
) -> None:
    try:
        document = json.loads(data.decode("utf-8-sig"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError(f"invalid HAR JSON: {source}: {exc}") from exc
    if isinstance(document, dict):
        add_har_document(inventory, document, source, all_hosts=all_hosts)


def scan_printable_blob(
    inventory: dict[tuple[str, str, str], Endpoint],
    data: bytes,
    source: str,
    *,
    all_hosts: bool,
    allow_relative: bool = True,
) -> None:
    seen: set[tuple[str, str, tuple[str, ...]]] = set()
    for run in PRINTABLE_RE.findall(data):
        for match in URL_RE.finditer(run):
            raw = match.group(0).decode("ascii", "ignore").rstrip(".,;:)]}")
            parts = urlsplit(raw)
            host = (parts.hostname or "").lower()
            if not host or (not all_hosts and not is_poyp_host(host)):
                continue
            if parts.path.startswith("//"):
                continue
            path = normalize_path(parts.path)
            if host in {"api.poyp.app", "auth.poyp.app", "poyp.app"} and path in {"/", "/api"}:
                continue
            query_keys = tuple(sorted({name for name, _ in parse_qsl(parts.query, keep_blank_values=True)}))
            marker = (host, path, query_keys)
            if marker in seen:
                continue
            seen.add(marker)
            merge_endpoint(
                inventory,
                Endpoint(
                    host=host,
                    path=path,
                    query_keys=set(query_keys),
                    sources={source},
                    evidence={"static"},
                    occurrences=1,
                ),
            )

        if not allow_relative:
            continue

        for match in API_PATH_RE.finditer(run):
            raw_path = match.group(0).decode("ascii", "ignore").rstrip(".,;:)]}")
            path_text, _, query = raw_path.partition("?")
            path = normalize_path(path_text)
            query_keys = tuple(
                sorted(
                    {
                        item.split("=", 1)[0]
                        for item in query.split("&")
                        if item and item.split("=", 1)[0]
                    }
                )
            )
            marker = ("api.poyp.app", path, query_keys)
            if marker in seen:
                continue
            seen.add(marker)
            host = "auth.poyp.app" if path.startswith("/auth/v1/") else "api.poyp.app"
            merge_endpoint(
                inventory,
                Endpoint(
                    host=host,
                    path=path,
                    query_keys=set(query_keys),
                    sources={source},
                    evidence={"static"},
                    occurrences=1,
                ),
            )


def split_route(raw_path: str) -> tuple[str, set[str]]:
    path_text, _, query = raw_path.partition("?")
    query_keys = {
        item.split("=", 1)[0]
        for item in query.split("&")
        if item and item.split("=", 1)[0]
    }
    return normalize_path(path_text), query_keys


def scan_decompiled_calls(
    inventory: dict[tuple[str, str, str], Endpoint],
    text: str,
    source: str,
) -> None:
    """Extract high-confidence method/path pairs from hermes-dec decompiler output."""

    lines = text.splitlines()
    for index, line in enumerate(lines):
        method_match = DECOMPILED_METHOD_RE.match(line)
        if not method_match:
            continue
        method_register, method = method_match.groups()

        options_register: str | None = None
        method_prop_index = -1
        for offset in range(index + 1, min(index + 8, len(lines))):
            prop_match = DECOMPILED_METHOD_PROP_RE.match(lines[offset])
            if prop_match and prop_match.group(2) == method_register:
                options_register = prop_match.group(1)
                method_prop_index = offset
                break
        if options_register is None:
            continue

        for route_index in range(method_prop_index + 1, min(method_prop_index + 14, len(lines))):
            route_match = DECOMPILED_ROUTE_RE.match(lines[route_index])
            if not route_match:
                continue
            route_register, raw_path = route_match.groups()
            if not raw_path.startswith("/") or raw_path.startswith("//"):
                continue

            call_confirmed = False
            for call_index in range(route_index + 1, min(route_index + 5, len(lines))):
                compact = lines[call_index].replace(" ", "")
                if ".bind(" not in compact:
                    continue
                if f"({route_register},{options_register})" in compact:
                    call_confirmed = True
                    break
            if not call_confirmed:
                continue

            path, query_keys = split_route(raw_path)
            if not path.startswith("/api/"):
                path = "/api" + path
            merge_endpoint(
                inventory,
                Endpoint(
                    host="api.poyp.app",
                    path=path,
                    method=method,
                    query_keys=query_keys,
                    sources={source},
                    evidence={"static"},
                    occurrences=1,
                ),
            )
            break


def should_scan_member(name: str) -> bool:
    lower = name.lower()
    if lower == "resources.arsc":
        return True
    if lower.startswith("assets/") or lower.startswith("res/raw/"):
        return True
    if Path(lower).suffix in SCAN_SUFFIXES:
        return True
    return Path(lower).name.startswith("classes") and lower.endswith(".dex")


def scan_apk_zip(
    inventory: dict[tuple[str, str, str], Endpoint],
    archive: zipfile.ZipFile,
    source: str,
    *,
    all_hosts: bool,
) -> None:
    for info in archive.infolist():
        if info.is_dir() or info.file_size > MAX_MEMBER_SIZE or not should_scan_member(info.filename):
            continue
        try:
            data = archive.read(info)
        except (OSError, RuntimeError, zipfile.BadZipFile):
            continue
        scan_printable_blob(
            inventory,
            data,
            f"{source}!{info.filename}",
            all_hosts=all_hosts,
            # A bare /api/... string inside an APK can belong to any bundled SDK.
            # Without host provenance, attributing it to api.poyp.app is unsafe.
            allow_relative=False,
        )


def scan_archive_path(
    inventory: dict[tuple[str, str, str], Endpoint],
    path: Path,
    *,
    all_hosts: bool,
) -> None:
    suffixes = [suffix.lower() for suffix in path.suffixes]
    if suffixes[-2:] == [".har", ".zip"]:
        with zipfile.ZipFile(path) as archive:
            for info in archive.infolist():
                if info.is_dir() or not info.filename.lower().endswith(".har"):
                    continue
                load_har_bytes(
                    inventory,
                    archive.read(info),
                    f"{path.name}!{info.filename}",
                    all_hosts=all_hosts,
                )
        return

    suffix = path.suffix.lower()
    if suffix == ".har":
        load_har_bytes(inventory, path.read_bytes(), path.name, all_hosts=all_hosts)
        return

    if suffix == ".apk":
        with zipfile.ZipFile(path) as archive:
            scan_apk_zip(inventory, archive, path.name, all_hosts=all_hosts)
        return

    if suffix == ".xapk":
        with zipfile.ZipFile(path) as outer:
            for info in outer.infolist():
                if info.is_dir() or not info.filename.lower().endswith(".apk"):
                    continue
                with zipfile.ZipFile(io.BytesIO(outer.read(info))) as inner:
                    scan_apk_zip(
                        inventory,
                        inner,
                        f"{path.name}!{info.filename}",
                        all_hosts=all_hosts,
                    )
        return

    data = path.read_bytes()
    decompiled_detected = False
    if suffix in {".js", ".txt"}:
        try:
            text = data.decode("utf-8")
        except UnicodeDecodeError:
            text = ""
        if "['method']" in text and "// Environment:" in text:
            decompiled_detected = True
            scan_decompiled_calls(inventory, text, path.name)
    scan_printable_blob(
        inventory,
        data,
        path.name,
        all_hosts=all_hosts,
        allow_relative=not decompiled_detected,
    )


def parse_known_routes(path: Path | None) -> set[str]:
    if path is None or not path.exists():
        return set()
    return {normalize_path(match.group(2)) for match in DOC_ROUTE_RE.finditer(path.read_text(encoding="utf-8"))}


def records(inventory: dict[tuple[str, str, str], Endpoint]) -> list[dict[str, Any]]:
    method_paths = {
        (endpoint.host, endpoint.path)
        for endpoint in inventory.values()
        if endpoint.method is not None
    }
    endpoints = [
        endpoint
        for endpoint in inventory.values()
        if endpoint.method is not None or (endpoint.host, endpoint.path) not in method_paths
    ]
    return [endpoint.as_dict() for endpoint in sorted(endpoints, key=lambda item: item.key())]


def write_json(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(rows, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "method",
                "host",
                "path",
                "query_keys",
                "body_keys",
                "statuses",
                "source",
                "confidence",
                "occurrences",
            ],
        )
        writer.writeheader()
        for row in rows:
            flat = dict(row)
            for key in ("query_keys", "body_keys", "statuses", "source"):
                flat[key] = ";".join(str(value) for value in row[key])
            writer.writerow(flat)


def write_markdown(path: Path, rows: list[dict[str, Any]], known_routes: set[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    static_only = [row for row in rows if row["confidence"] == "static" and row["path"] not in known_routes]
    lines = [
        "# Endpoint inventory",
        "",
        "Generated from local evidence. `observed` means HAR traffic; `static` means an APK/XAPK/string match and does not establish method, request shape, or server behavior.",
        "",
        "| Evidence | Method | Host | Path | Query keys | Body keys | Statuses |",
        "| --- | --- | --- | --- | --- | --- | --- |",
    ]
    for row in rows:
        lines.append(
            "| {confidence} | {method} | `{host}` | `{path}` | {query} | {body} | {statuses} |".format(
                confidence=row["confidence"],
                method=row["method"] or "?",
                host=row["host"],
                path=row["path"],
                query=", ".join(f"`{item}`" for item in row["query_keys"]) or "-",
                body=", ".join(f"`{item}`" for item in row["body_keys"]) or "-",
                statuses=", ".join(str(item) for item in row["statuses"]) or "-",
            )
        )

    if known_routes:
        lines.extend(["", "## Static-only paths vs documented observed routes", ""])
        if static_only:
            lines.extend(f"- `{row['path']}`" for row in static_only)
        else:
            lines.append("No static-only paths found.")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def default_known_doc() -> Path | None:
    candidate = Path("docs/endpoints.md")
    return candidate if candidate.exists() else None


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Build a secret-safe POYP endpoint inventory from HAR/APK/XAPK evidence."
    )
    parser.add_argument("inputs", nargs="+", type=Path, help="HAR, HAR.ZIP, APK, XAPK, or extracted file")
    parser.add_argument("--json", dest="json_path", type=Path, help="Write JSON inventory")
    parser.add_argument("--csv", dest="csv_path", type=Path, help="Write CSV inventory")
    parser.add_argument("--markdown", dest="markdown_path", type=Path, help="Write Markdown inventory")
    parser.add_argument(
        "--known-doc",
        type=Path,
        default=default_known_doc(),
        help="Observed endpoint Markdown used for static-only diff (default: docs/endpoints.md)",
    )
    parser.add_argument("--all-hosts", action="store_true", help="Include non-poyp.app URL hosts")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    inventory: dict[tuple[str, str, str], Endpoint] = {}
    for path in args.inputs:
        if not path.exists():
            raise SystemExit(f"input not found: {path}")
        scan_archive_path(inventory, path, all_hosts=args.all_hosts)

    rows = records(inventory)
    known_routes = parse_known_routes(args.known_doc)
    if args.json_path:
        write_json(args.json_path, rows)
    if args.csv_path:
        write_csv(args.csv_path, rows)
    if args.markdown_path:
        write_markdown(args.markdown_path, rows, known_routes)

    observed = sum(1 for row in rows if row["confidence"] == "observed")
    static = len(rows) - observed
    static_only = sum(
        1 for row in rows if row["confidence"] == "static" and row["path"] not in known_routes
    )
    print(
        f"endpoints={len(rows)} observed={observed} static={static} "
        f"static_only_vs_docs={static_only}"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
