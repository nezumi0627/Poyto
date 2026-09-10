import importlib.util
import io
import sys
import zipfile
from pathlib import Path


def _load_endpoint_inventory():
    path = Path(__file__).resolve().parents[1] / "tools" / "endpoint_inventory.py"
    spec = importlib.util.spec_from_file_location("poyto_endpoint_inventory", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


endpoint_inventory = _load_endpoint_inventory()
Endpoint = endpoint_inventory.Endpoint
parse_known_routes = endpoint_inventory.parse_known_routes
records = endpoint_inventory.records
scan_apk_zip = endpoint_inventory.scan_apk_zip
scan_decompiled_calls = endpoint_inventory.scan_decompiled_calls
scan_printable_blob = endpoint_inventory.scan_printable_blob


def test_scan_decompiled_calls_recovers_method_and_normalized_route() -> None:
    inventory: dict[tuple[str, str, str], Endpoint] = {}
    text = """// Environment: r0:4
    r1 = 'POST';
    r2['method'] = r1;
    r3 = 0;
    r4 = '/me/login-streak/claim?source=login';
    r5 = r0.bind(r6)(r4, r2);
    """

    scan_decompiled_calls(inventory, text, "decompiled.js")

    assert records(inventory) == [
        {
            "method": "POST",
            "host": "api.poyp.app",
            "path": "/api/me/login-streak/claim",
            "query_keys": ["source"],
            "body_keys": [],
            "statuses": [],
            "source": ["decompiled.js"],
            "functions": [],
            "locations": ["decompiled.js:6"],
            "confidence": "static-call",
            "occurrences": 1,
        }
    ]


def test_scan_decompiled_calls_requires_route_and_options_in_same_call() -> None:
    inventory: dict[tuple[str, str, str], Endpoint] = {}
    text = """// Environment: r0:4
    r1 = 'POST';
    r2['method'] = r1;
    r4 = '/me/login-streak/claim';
    r5 = r0.bind(r6)(r4, r7);
    """

    scan_decompiled_calls(inventory, text, "decompiled.js")

    assert records(inventory) == []


def test_scan_decompiled_calls_recovers_default_get_and_query_keys() -> None:
    inventory: dict[tuple[str, str, str], Endpoint] = {}
    text = """r0 = function() { // Original name: _fetchFollowers, environment: r2
    r4 = {};
    r7 = r4.set;
    r5 = 'cursor';
    r5 = r7.bind(r4)(r5, r6);
    r7 = r4.set;
    r5 = 'limit';
    r5 = r7.bind(r4)(r5, r6);
    r7 = r4.toString;
    r7 = r7.bind(r4)();
    r8 = '?';
    r9 = r10.concat;
    r8 = r9.bind(r8)(r7);
    r9 = r10.concat;
    r5 = '/users/';
    r7 = a0;
    r1 = '/followers';
    r1 = r9.bind(r5)(r7, r1, r8);
    r1 = r3.bind(undefined)(r1);
    """

    scan_decompiled_calls(inventory, text, "decompiled.js")

    rows = records(inventory)
    assert len(rows) == 1
    assert rows[0]["method"] == "GET"
    assert rows[0]["path"] == "/api/users/{userId}/followers"
    assert rows[0]["query_keys"] == ["cursor", "limit"]


def test_scan_decompiled_calls_preserves_concat_when_destination_is_receiver() -> None:
    inventory: dict[tuple[str, str, str], Endpoint] = {}
    text = """r0 = function() { // Original name: _fetchFollowStatus, environment: r2
    r4 = '/users/';
    r6 = a0;
    r5 = r10.concat;
    r4 = r5.bind(r4)(r6, '/follow-status');
    r4 = r3.bind(undefined)(r4);
    """

    scan_decompiled_calls(inventory, text, "decompiled.js")

    rows = records(inventory)
    assert len(rows) == 1
    assert rows[0]["path"] == "/api/users/{userId}/follow-status"


def test_scan_decompiled_calls_recovers_json_body_keys() -> None:
    inventory: dict[tuple[str, str, str], Endpoint] = {}
    text = """r0 = function() { // Original name: _reportComment, environment: r2
    r1 = {};
    r2 = a0;
    r1['reason'] = r2;
    r3 = a1;
    r1['description'] = r3;
    r4 = r5.stringify;
    r4 = r4.bind(r5)(r1);
    r6 = {};
    r7 = 'POST';
    r6['method'] = r7;
    r6['body'] = r4;
    r8 = '/comments/';
    r9 = a2;
    r10 = r11.concat;
    r8 = r10.bind(r8)(r9, '/report');
    r12 = r13.bind(undefined)(r8, r6);
    """

    scan_decompiled_calls(inventory, text, "decompiled.js")

    rows = records(inventory)
    assert len(rows) == 1
    assert rows[0]["path"] == "/api/comments/{commentId}/report"
    assert rows[0]["body_keys"] == ["description", "reason"]


def test_default_get_detection_rejects_unrelated_sdk_route() -> None:
    inventory: dict[tuple[str, str, str], Endpoint] = {}
    text = """r0 = function() { // Original name: _fetchSegment, environment: r2
    r1 = '/api/broadcast';
    r1 = r3.bind(undefined)(r1);
    """

    scan_decompiled_calls(inventory, text, "decompiled.js")

    assert records(inventory) == []


def test_parse_known_routes_requires_exact_http_method(tmp_path: Path) -> None:
    known_doc = tmp_path / "endpoints.md"
    known_doc.write_text(
        "`GET /api/users/{userId}/follow`\n"
        "This route is APK-static-only: `POST /api/trades/quote`.\n"
        "- `GET /api/users/{userId}/follow`\n"
        "`/api/methodless-note`\n",
        encoding="utf-8",
    )

    assert parse_known_routes(known_doc) == {("GET", "/api/users/{userId}/follow")}


def test_scan_decompiled_calls_labels_common_dynamic_ids() -> None:
    inventory: dict[tuple[str, str, str], Endpoint] = {}
    text = """r0 = function() { // Original name: _followTeam, environment: r2
    r1 = {};
    r2 = 'POST';
    r1['method'] = r2;
    r3 = '/teams/';
    r4 = a0;
    r5 = r6.concat;
    r3 = r5.bind(r3)(r4, '/follow');
    r7 = r8.bind(undefined)(r3, r1);
    """

    scan_decompiled_calls(inventory, text, "decompiled.js")

    rows = records(inventory)
    assert len(rows) == 1
    assert rows[0]["path"] == "/api/teams/{teamId}/follow"


def test_records_suppresses_methodless_duplicate_for_same_route() -> None:
    inventory = {
        ("api.poyp.app", "", "/api/trades/quote"): Endpoint(
            host="api.poyp.app",
            path="/api/trades/quote",
            sources={"bundle"},
            evidence={"static-string"},
            occurrences=1,
        ),
        ("api.poyp.app", "POST", "/api/trades/quote"): Endpoint(
            host="api.poyp.app",
            path="/api/trades/quote",
            method="POST",
            sources={"decompiled.js"},
            evidence={"static-call"},
            occurrences=1,
        ),
    }

    rows = records(inventory)

    assert len(rows) == 1
    assert rows[0]["method"] == "POST"


def test_apk_scan_does_not_attribute_bare_sdk_api_paths_to_poyp() -> None:
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as archive:
        archive.writestr("assets/main.jsbundle", b"third-party /api/broadcast endpoint")
    buffer.seek(0)

    inventory: dict[tuple[str, str, str], Endpoint] = {}
    with zipfile.ZipFile(buffer) as archive:
        scan_apk_zip(inventory, archive, "app.apk", all_hosts=False)

    assert records(inventory) == []


def test_printable_scan_rejects_fused_base_url_string_table_junk() -> None:
    inventory: dict[tuple[str, str, str], Endpoint] = {}

    scan_printable_blob(
        inventory,
        b"https://poyp.app///main.jsbundleUrlastSyncUserLTVInVirtualCurrency",
        "bundle",
        all_hosts=False,
        allow_relative=False,
    )

    assert records(inventory) == []
