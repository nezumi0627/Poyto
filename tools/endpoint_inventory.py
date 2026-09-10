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
    r"^\s*-\s+`(?:(GET|POST|PUT|DELETE|PATCH|HEAD|OPTIONS)\s+)?(/(?:api|auth/v1)/[^`?\s]+)(?:\?[^`]*)?`",
    re.MULTILINE,
)
DECOMPILED_METHOD_RE = re.compile(
    r"^\s*(r\d+) = '(GET|POST|PUT|DELETE|PATCH|HEAD|OPTIONS)';\s*$"
)
DECOMPILED_METHOD_PROP_RE = re.compile(r"^\s*(r\d+)\['method'\] = (r\d+);\s*$")
DECOMPILED_ROUTE_RE = re.compile(r"^\s*(r\d+) = '(/[^'\r\n]+)';\s*$")
DECOMPILED_STRING_RE = re.compile(r"^\s*(r\d+) = '([^'\r\n]*)';\s*$")
DECOMPILED_COPY_RE = re.compile(r"^\s*(r\d+) = (r\d+);\s*$")
DECOMPILED_ARG_COPY_RE = re.compile(r"^\s*(r\d+) = a\d+;\s*$")
DECOMPILED_PROP_RE = re.compile(r"^\s*(r\d+) = (r\d+)\.([A-Za-z_$][\w$]*);\s*$")
DECOMPILED_EMPTY_OBJECT_RE = re.compile(r"^\s*(r\d+) = \{\};\s*$")
DECOMPILED_OBJECT_PROP_RE = re.compile(r"^\s*(r\d+)\['([^']+)'\] = (r\d+);\s*$")
DECOMPILED_BIND_CALL_RE = re.compile(
    r"^\s*(r\d+) = (r\d+)\.bind\((r\d+|undefined)\)\((.*)\);\s*$"
)
DECOMPILED_FUNCTION_RE = re.compile(r"Original name: ([^,]+),")

POYP_API_ROOTS = {
    "adjust-attribution",
    "campaign-banners",
    "check-username",
    "comments",
    "eraberu-pay",
    "faqs",
    "global-chat",
    "home-sections",
    "home-tabs",
    "interests",
    "leaderboard",
    "live-moments",
    "live-stats",
    "markets",
    "me",
    "onboarding",
    "prices",
    "safety",
    "search",
    "settlements",
    "teams",
    "timeline",
    "trades",
    "users",
    "walking-challenge",
    "worldcup",
}

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
    functions: set[str] = field(default_factory=set)
    locations: set[str] = field(default_factory=set)
    evidence: set[str] = field(default_factory=set)
    occurrences: int = 0

    def key(self) -> tuple[str, str, str]:
        return (self.host, self.method or "", self.path)

    def as_dict(self) -> dict[str, Any]:
        if "observed" in self.evidence:
            confidence = "observed"
        elif "static-call" in self.evidence:
            confidence = "static-call"
        else:
            confidence = "static-string"
        return {
            "method": self.method,
            "host": self.host,
            "path": self.path,
            "query_keys": sorted(self.query_keys),
            "body_keys": sorted(self.body_keys),
            "statuses": sorted(self.statuses),
            "source": sorted(self.sources),
            "functions": sorted(self.functions),
            "locations": sorted(self.locations),
            "confidence": confidence,
            "occurrences": self.occurrences,
        }


def normalize_path(path: str) -> str:
    path = UUID_RE.sub("{uuid}", path)
    path = LONG_NUMERIC_SEGMENT_RE.sub("{id}", path)
    return path.rstrip("/\"'`,;)]") or "/"


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
    existing.functions.update(endpoint.functions)
    existing.locations.update(endpoint.locations)
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
                    evidence={"static-string"},
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
                    evidence={"static-string"},
                    occurrences=1,
                ),
            )


def split_route(raw_path: str) -> tuple[str, set[str]]:
    path_text, _, query = raw_path.partition("?")
    query_keys = {
        item.split("=", 1)[0]
        for item in query.split("&")
        if item and item.split("=", 1)[0] and not item.startswith("{")
    }
    return normalize_path(path_text), query_keys


def split_decompiled_args(raw: str) -> list[str]:
    """Split the simple register/literal argument lists emitted by hermes-dec."""

    result: list[str] = []
    current: list[str] = []
    quote: str | None = None
    depth = 0
    for char in raw:
        if quote is not None:
            current.append(char)
            if char == quote:
                quote = None
            continue
        if char in {"'", '"'}:
            quote = char
            current.append(char)
        elif char in "([{":
            depth += 1
            current.append(char)
        elif char in ")]}":
            depth = max(0, depth - 1)
            current.append(char)
        elif char == "," and depth == 0:
            result.append("".join(current).strip())
            current = []
        else:
            current.append(char)
    if current:
        result.append("".join(current).strip())
    return result


def label_dynamic_segments(path: str, function_name: str | None) -> str:
    """Give common POYP path parameters stable names instead of `{dynamic}`."""

    segment_labels = {
        "campaign-results": "campaignResultId",
        "markets": "marketId",
        "users": "userId",
        "comments": "commentId",
        "messages": "messageId",
        "teams": "teamId",
        "entries": "entryId",
        "prices": "asset",
        "interests": "category",
        "missions": "slug",
        "notifications": "notificationId",
        "check-username": "username",
        "live-stats": "id",
    }
    parts = path.split("/")
    for index, part in enumerate(parts):
        if part != "{dynamic}":
            continue
        previous = parts[index - 1] if index else ""
        label = segment_labels.get(previous)
        if label is None and function_name:
            lowered = function_name.lower()
            for needle, candidate in (
                ("market", "marketId"),
                ("comment", "commentId"),
                ("user", "userId"),
                ("asset", "asset"),
                ("price", "asset"),
                ("interest", "category"),
                ("mission", "slug"),
            ):
                if needle in lowered:
                    label = candidate
                    break
        parts[index] = "{" + (label or "param") + "}"
    return "/".join(parts)


def is_default_get_call(function_name: str | None, raw_route: str) -> bool:
    """Identify POYP request-helper calls that omit options and therefore use GET."""

    if not function_name or not raw_route.startswith("/") or raw_route.startswith("//"):
        return False
    if not (
        function_name.startswith("_fetch")
        or function_name == "_getLoginStreak"
        or function_name.startswith("_check")
        or function_name == "_validateReferralCode"
    ):
        return False
    route_path = raw_route.split("?", 1)[0].strip("/")
    root = route_path.split("/", 1)[0] if route_path else ""
    return root in POYP_API_ROOTS


def scan_decompiled_dynamic_calls(
    inventory: dict[tuple[str, str, str], Endpoint],
    text: str,
    source: str,
) -> None:
    """Symbolically recover concat-built Hermes routes and obvious request metadata."""

    strings: dict[str, str] = {}
    string_query_keys: dict[str, set[str]] = {}
    function_kinds: dict[str, tuple[str, str | None]] = {}
    labels: dict[str, str] = {}
    methods: dict[str, str] = {}
    option_methods: dict[str, str] = {}
    option_body_keys: dict[str, set[str]] = {}
    object_keys: dict[str, set[str]] = {}
    query_object_keys: dict[str, set[str]] = {}
    serialized_body_keys: dict[str, set[str]] = {}
    current_function: str | None = None
    emitted: set[tuple[str, str]] = set()

    def clear_register(register: str) -> None:
        for mapping in (
            strings,
            string_query_keys,
            function_kinds,
            labels,
            methods,
            option_methods,
            option_body_keys,
            object_keys,
            query_object_keys,
            serialized_body_keys,
        ):
            mapping.pop(register, None)

    def copy_register(destination: str, source_register: str) -> None:
        clear_register(destination)
        if source_register in strings:
            strings[destination] = strings[source_register]
        if source_register in string_query_keys:
            string_query_keys[destination] = set(string_query_keys[source_register])
        if source_register in function_kinds:
            function_kinds[destination] = function_kinds[source_register]
        if source_register in labels:
            labels[destination] = labels[source_register]
        if source_register in methods:
            methods[destination] = methods[source_register]
        if source_register in option_methods:
            option_methods[destination] = option_methods[source_register]
        if source_register in option_body_keys:
            option_body_keys[destination] = set(option_body_keys[source_register])
        if source_register in object_keys:
            object_keys[destination] = set(object_keys[source_register])
        if source_register in query_object_keys:
            query_object_keys[destination] = set(query_object_keys[source_register])
        if source_register in serialized_body_keys:
            serialized_body_keys[destination] = set(serialized_body_keys[source_register])

    def symbol(argument: str) -> tuple[str | None, set[str]]:
        if argument in strings:
            return strings[argument], set(string_query_keys.get(argument, set()))
        if argument in labels:
            return "{" + labels[argument] + "}", set()
        if len(argument) >= 2 and argument[0] == argument[-1] and argument[0] in {"'", '"'}:
            return argument[1:-1], set()
        return None, set()

    for line_number, line in enumerate(text.splitlines(), start=1):
        function_match = DECOMPILED_FUNCTION_RE.search(line)
        if function_match:
            name = function_match.group(1)
            if name not in {"?anon_0_", "<anonymous>"}:
                current_function = name
            strings.clear()
            string_query_keys.clear()
            function_kinds.clear()
            labels.clear()
            methods.clear()
            option_methods.clear()
            option_body_keys.clear()
            object_keys.clear()
            query_object_keys.clear()
            serialized_body_keys.clear()
            continue

        empty_match = DECOMPILED_EMPTY_OBJECT_RE.match(line)
        if empty_match:
            register = empty_match.group(1)
            clear_register(register)
            object_keys[register] = set()
            continue

        method_match = DECOMPILED_METHOD_RE.match(line)
        if method_match:
            register, method = method_match.groups()
            clear_register(register)
            strings[register] = method
            methods[register] = method
            continue

        route_match = DECOMPILED_ROUTE_RE.match(line)
        if route_match:
            register, raw_path = route_match.groups()
            clear_register(register)
            strings[register] = raw_path
            continue

        string_match = DECOMPILED_STRING_RE.match(line)
        if string_match:
            register, value = string_match.groups()
            clear_register(register)
            strings[register] = value
            continue

        arg_match = DECOMPILED_ARG_COPY_RE.match(line)
        if arg_match:
            register = arg_match.group(1)
            clear_register(register)
            labels[register] = "dynamic"
            continue

        copy_match = DECOMPILED_COPY_RE.match(line)
        if copy_match:
            copy_register(*copy_match.groups())
            continue

        property_match = DECOMPILED_PROP_RE.match(line)
        if property_match:
            destination, base, prop = property_match.groups()
            clear_register(destination)
            if prop in {"encodeURIComponent", "concat", "stringify"}:
                function_kinds[destination] = (prop, base)
            elif prop in {"append", "set", "toString"}:
                function_kinds[destination] = (prop, base)
            else:
                # Property values are often fed directly into URL concat
                # (for example options.tf).  Keeping the property name lets
                # us preserve the route even when the concrete value is only
                # known at runtime.
                labels[destination] = prop
            continue

        object_prop_match = DECOMPILED_OBJECT_PROP_RE.match(line)
        if object_prop_match:
            target, prop, value_register = object_prop_match.groups()
            if target in object_keys and prop not in {"method", "body", "headers"}:
                object_keys[target].add(prop)
            if prop == "method" and value_register in methods:
                option_methods[target] = methods[value_register]
            elif prop == "body":
                option_body_keys[target] = set(serialized_body_keys.get(value_register, set()))
            continue

        call_match = DECOMPILED_BIND_CALL_RE.match(line)
        if not call_match:
            continue
        destination, function_register, bound_register, raw_args = call_match.groups()
        args = split_decompiled_args(raw_args)
        kind_info = function_kinds.get(function_register)

        # A common hermes-dec shape reuses the output register as either the
        # concat receiver or one of its arguments, e.g.
        # `r4 = concat.bind(r4)(r7, r1)`.  Snapshot every input before the
        # destination is overwritten so symbolic route construction does not
        # accidentally erase its own prefix/suffix.
        bound_symbol = symbol(bound_register)
        arg_symbols = [symbol(argument) for argument in args]
        arg_object_keys = [set(object_keys.get(argument, set())) for argument in args]
        kind_base = kind_info[1] if kind_info is not None else None
        base_query_object_keys = set(query_object_keys.get(kind_base or "", set()))

        # Detect the actual API helper call before the destination register is overwritten.
        if len(args) >= 2 and args[0].startswith("r") and args[1].startswith("r"):
            route_register, options_register = args[0], args[1]
            raw_route = strings.get(route_register)
            method = option_methods.get(options_register)
            if raw_route and method and raw_route.startswith("/") and not raw_route.startswith("//"):
                path, query_keys = split_route(raw_route)
                query_keys.update(string_query_keys.get(route_register, set()))
                if not path.startswith("/api/"):
                    path = "/api" + path
                path = label_dynamic_segments(path, current_function)
                marker = (method, path)
                if marker not in emitted:
                    emitted.add(marker)
                    merge_endpoint(
                        inventory,
                        Endpoint(
                            host="api.poyp.app",
                            path=path,
                            method=method,
                            query_keys=query_keys,
                            body_keys=set(option_body_keys.get(options_register, set())),
                            sources={source},
                            functions={current_function} if current_function else set(),
                            locations={f"{source}:{line_number}"},
                            evidence={"static-call"},
                            occurrences=1,
                        ),
                    )

        # The shared POYP request helper defaults to GET when no options object is
        # supplied. Hermes emits these calls as helper.bind(undefined)(route).
        # Restrict the inference to known POYP API helper functions and route roots
        # so unrelated bundled SDK calls are not attributed to api.poyp.app.
        if len(args) == 1 and args[0].startswith("r"):
            route_register = args[0]
            raw_route = strings.get(route_register)
            if raw_route and is_default_get_call(current_function, raw_route):
                path, query_keys = split_route(raw_route)
                query_keys.update(string_query_keys.get(route_register, set()))
                if not path.startswith("/api/"):
                    path = "/api" + path
                path = label_dynamic_segments(path, current_function)
                marker = ("GET", path)
                if marker not in emitted:
                    emitted.add(marker)
                    merge_endpoint(
                        inventory,
                        Endpoint(
                            host="api.poyp.app",
                            path=path,
                            method="GET",
                            query_keys=query_keys,
                            sources={source},
                            functions={current_function} if current_function else set(),
                            locations={f"{source}:{line_number}"},
                            evidence={"static-call"},
                            occurrences=1,
                        ),
                    )

        clear_register(destination)
        if kind_info is None:
            continue
        kind, base = kind_info
        if kind == "encodeURIComponent" and args:
            label = labels.get(args[0], "dynamic")
            strings[destination] = "{" + label + "}"
            labels[destination] = label
        elif kind == "concat":
            base_text, base_query_keys = bound_symbol
            pieces: list[str] = []
            query_keys = set(base_query_keys)
            if base_text is not None:
                pieces.append(base_text)
                for argument, (value, argument_query_keys) in zip(args, arg_symbols, strict=True):
                    if value is None:
                        # Query strings are frequently produced by a helper
                        # call that hermes-dec cannot name.  A register-valued
                        # concat argument is still enough to retain the path;
                        # split_route() deliberately ignores this placeholder
                        # as an unknown query key.
                        if argument.startswith("r"):
                            value = "{param}"
                        else:
                            pieces = []
                            break
                    pieces.append(value)
                    query_keys.update(argument_query_keys)
            if pieces:
                strings[destination] = "".join(pieces)
                string_query_keys[destination] = query_keys
        elif kind in {"append", "set"} and base is not None and args:
            key = arg_symbols[0][0]
            if key:
                query_object_keys.setdefault(base, set()).add(key)
        elif kind == "toString" and base is not None:
            strings[destination] = "{query}"
            string_query_keys[destination] = base_query_object_keys
        elif kind == "stringify" and args:
            serialized_body_keys[destination] = arg_object_keys[0]


def scan_decompiled_calls(
    inventory: dict[tuple[str, str, str], Endpoint],
    text: str,
    source: str,
) -> None:
    """Extract high-confidence method/path pairs from hermes-dec decompiler output."""
    scan_decompiled_dynamic_calls(inventory, text, source)


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


def parse_known_routes(path: Path | None) -> set[tuple[str, str]]:
    if path is None or not path.exists():
        return set()
    return {
        (match.group(1), normalize_path(match.group(2)))
        for match in DOC_ROUTE_RE.finditer(path.read_text(encoding="utf-8"))
        if match.group(1)
    }


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
                "functions",
                "locations",
                "confidence",
                "occurrences",
            ],
        )
        writer.writeheader()
        for row in rows:
            flat = dict(row)
            for key in ("query_keys", "body_keys", "statuses", "source", "functions", "locations"):
                flat[key] = ";".join(str(value) for value in row[key])
            writer.writerow(flat)


def write_markdown(
    path: Path,
    rows: list[dict[str, Any]],
    known_routes: set[tuple[str, str]],
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    static_only = [
        row
        for row in rows
        if row["confidence"] != "observed" and (row["method"], row["path"]) not in known_routes
    ]
    lines = [
        "# Endpoint inventory",
        "",
        "Generated from local evidence. `observed` means HAR traffic; `static-call` means method/path were recovered from a decompiled Hermes request-helper call; `static-string` means only a raw APK/XAPK/string match. Static evidence does not establish runtime reachability or server behavior.",
        "",
        "| Evidence | Method | Host | Path | Query keys | Body keys | APK function | Decompiled call | Documented observed | Statuses |",
        "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    for row in rows:
        documented = (row["method"], row["path"]) in known_routes
        lines.append(
            "| {confidence} | {method} | `{host}` | `{path}` | {query} | {body} | {functions} | {locations} | {documented} | {statuses} |".format(
                confidence=row["confidence"],
                method=row["method"] or "?",
                host=row["host"],
                path=row["path"],
                query=", ".join(f"`{item}`" for item in row["query_keys"]) or "-",
                body=", ".join(f"`{item}`" for item in row["body_keys"]) or "-",
                functions=", ".join(f"`{item}`" for item in row["functions"]) or "-",
                locations=", ".join(f"`{item}`" for item in row["locations"]) or "-",
                documented="yes" if documented else "no",
                statuses=", ".join(str(item) for item in row["statuses"]) or "-",
            )
        )

    if known_routes:
        lines.extend(["", "## Static-only paths vs documented observed routes", ""])
        if static_only:
            lines.extend(f"- `{row['method']} {row['path']}`" for row in static_only)
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
    static_call = sum(1 for row in rows if row["confidence"] == "static-call")
    static_string = sum(1 for row in rows if row["confidence"] == "static-string")
    static_only = sum(
        1
        for row in rows
        if row["confidence"] != "observed" and (row["method"], row["path"]) not in known_routes
    )
    print(
        f"endpoints={len(rows)} observed={observed} static_call={static_call} static_string={static_string} "
        f"static_only_vs_docs={static_only}"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
