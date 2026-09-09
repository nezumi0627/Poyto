# Endpoint inventory workflow

`tools/endpoint_inventory.py` builds a secret-safe route inventory from authorized HAR captures and APK/XAPK static artifacts.

The evidence levels are intentionally separate:

- **observed** — the method/path/query/body-key/status combination came from HAR request/response traffic;
- **static** — a URL or `/api/...`/`/auth/v1/...` string was found in an APK/XAPK or extracted asset. Static evidence alone does not prove the HTTP method, request body, eligibility rules, or that the route is still reachable;
- **inferred** — remains a documentation category for behavior supported by external protocol knowledge rather than direct POYP evidence. The inventory tool does not automatically promote static strings to inferred or observed.

## Usage

```powershell
python tools/endpoint_inventory.py capture.har POYP.apk `
  --json .analysis/endpoints.json `
  --csv .analysis/endpoints.csv `
  --markdown .analysis/endpoints.md
```

XAPK files are opened as ZIP archives and every contained APK is scanned. APK scanning includes React Native/Expo assets, `classes*.dex`, resources, text-like assets, and native libraries where printable URLs may exist. Bare relative `/api/...` strings from packaged APK members are intentionally ignored because bundled SDKs can contain unrelated API paths and there is no host provenance. No APK contents are committed by this workflow.

Hermes bytecode stores adjacent strings without normal text delimiters, so raw printable-string scanning is deliberately conservative. For stronger static evidence, decompile `assets/index.android.bundle` with `hermes-dec` and add the decompiled file as another input:

```powershell
pip install hermes-dec
hbc-decompiler index.android.bundle .analysis/decompiled.js
python tools/endpoint_inventory.py POYP.apk .analysis/decompiled.js `
  --markdown .analysis/endpoints.md
```

For hermes-dec output, the tool only records a method/path pair when it sees a nearby `METHOD -> options.method -> route -> helper(route, options)` call pattern. This is still classified as **static**, but is substantially stronger than a loose string-table match.

HAR output contains only route metadata: host, method, normalized path, query-key names, top-level request-body key names, response statuses, and source filename. Query/body values, headers, cookies, tokens, user payloads, and response bodies are not emitted.

By default only `poyp.app` hosts are included. Use `--all-hosts` only when you intentionally need third-party SDK traffic.

`--known-doc docs/endpoints.md` is enabled by default when that file exists. Markdown output then includes a **Static-only paths vs documented observed routes** section. Treat that section as a research queue, not as a list of supported Poyto endpoints.

## Recommended process

1. Generate an inventory from current HAR evidence.
2. Add the current APK/XAPK to the same run.
3. Review static-only paths and locate their call sites in JADX or the JavaScript/Hermes bundle.
4. Reproduce promising read-only requests with a user-owned session when safe.
5. Only after direct verification, move the route into `docs/endpoints.md` and add a client wrapper/test if useful.

Never commit raw HAR/APK/XAPK artifacts or generated output that contains private identifiers.
