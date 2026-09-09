import io
import zipfile

from tools.endpoint_inventory import (
    Endpoint,
    records,
    scan_apk_zip,
    scan_decompiled_calls,
    scan_printable_blob,
)


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
            "confidence": "static",
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


def test_records_suppresses_methodless_duplicate_for_same_route() -> None:
    inventory = {
        ("api.poyp.app", "", "/api/trades/quote"): Endpoint(
            host="api.poyp.app",
            path="/api/trades/quote",
            sources={"bundle"},
            evidence={"static"},
            occurrences=1,
        ),
        ("api.poyp.app", "POST", "/api/trades/quote"): Endpoint(
            host="api.poyp.app",
            path="/api/trades/quote",
            method="POST",
            sources={"decompiled.js"},
            evidence={"static"},
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
