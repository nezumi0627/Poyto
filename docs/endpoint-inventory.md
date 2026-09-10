# Endpoint inventory workflow

`tools/endpoint_inventory.py` builds a secret-safe route inventory from authorized HAR captures and APK/XAPK static artifacts.

The evidence levels are intentionally separate:

- **observed** — the method/path/query/body-key/status combination came from HAR request/response traffic;
- **static-call** — method/path were recovered from a decompiled Hermes request-helper call. This is stronger than a raw string hit because the client function and call-site are known, but it still does not prove current server reachability;
- **static-string** — only a URL or `/api/...`/`/auth/v1/...` string was found in an APK/XAPK or extracted asset. Treat this as weak/noisy evidence until a POYP request call-site is found;
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

For hermes-dec output, the scanner symbolically follows the common POYP request-building shapes instead of relying only on adjacent string matches. It reconstructs concat-built routes, labels common dynamic path segments, recovers query keys from URLSearchParams-like `set`/`toString` flows, and recovers top-level JSON body keys when the object/stringify flow is statically visible. For high-confidence POYP `_fetch*`/GET helpers, a route-only helper call is treated as the shared request helper's default GET behavior. The function-name and first-route-segment allowlists prevent unrelated bundled SDK routes from being attributed to `api.poyp.app`.

These results remain **static-call** evidence. A reconstructed method/path/request shape proves that the shipped client contains and calls that route shape; it does not prove that the server still accepts the route, that the current account is eligible, or that all runtime-only fields were recovered. Raw string-only hits remain **static-string** and should not be promoted just because they look like an API path.

HAR output contains only route metadata: host, method, normalized path, query-key names, top-level request-body key names, response statuses, and source filename. Query/body values, headers, cookies, tokens, user payloads, and response bodies are not emitted.

By default only `poyp.app` hosts are included. Use `--all-hosts` only when you intentionally need third-party SDK traffic.

`--known-doc docs/endpoints.md` is enabled by default when that file exists. Comparison uses the exact **HTTP method + normalized path** pair. Markdown output includes a `Documented observed` column and a **Static-only paths vs documented observed routes** section. Treat static-only entries as a research queue, not as already verified Poyto endpoints.

## Recommended process

1. Generate an inventory from current HAR evidence.
2. Add the current APK/XAPK to the same run.
3. Review static-only paths and require a concrete request-helper call site in JADX or the JavaScript/Hermes bundle before treating them as client API candidates.
4. Reproduce promising read-only requests with a user-owned session when safe.
5. Only after direct verification, move the route into `docs/endpoints.md` and add a client wrapper/test if useful.

Never commit raw HAR/APK/XAPK artifacts or generated output that contains private identifiers.
