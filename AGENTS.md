# AGENTS.md

This repository is intentionally friendly to AI-assisted maintenance, reverse-engineering, documentation, and testing.

The most important rule is simple: **do not confuse implementation with evidence**. Poyto is an unofficial client reconstructed from observed POYP traffic. Preserve the distinction between what was observed, what is inferred, and what is still unknown.

## Project goal

Poyto provides a small, typed Python client and CLI for POYP. It should remain:

- easy to audit against real request/response evidence
- easy to test without live credentials
- conservative about undocumented behavior
- explicit about state-changing operations
- safe around access tokens, refresh tokens, Apple credentials, cookies, and stable device identifiers
- usable on Python 3.10 through 3.14

## Read these files first

Before changing behavior, read the most relevant documents:

- `README.md` — user-facing overview
- `DISCLAIMER.md` — project scope, responsibility, and non-affiliation
- `docs/capabilities.md` — canonical supported-feature inventory and evidence levels
- `docs/known-gaps.md` — canonical do-not-claim / unsupported list
- `docs/endpoints.md` — directly observed route inventory
- `docs/authentication.md` — auth design
- `docs/refresh-tokens.md` — established vs inferred refresh behavior
- `docs/ad-rewards.md` — ad-reward request/response behavior
- `docs/service-model-and-legal-context.md` — source-backed POYP point/coin model and Japan legal context
- `docs/architecture.md` — module responsibilities
- `docs/python-api.md` — Python surface
- `docs/cli.md` — CLI surface
- `SECURITY.md` — credential handling

If code and docs disagree, inspect the implementation and tests, then fix stale documentation in the same change.

## Required context for prediction-market actions

Before implementing, reviewing, or classifying an operation that buys, sells, settles, or otherwise changes a POYP prediction position, read `docs/service-model-and-legal-context.md`.

Use the documented service facts as context: POYP Terms describe prediction points as acquired free of charge through login/advertising activity and usable only inside the prediction market; reward coins are a separate unit granted for correct predictions and exchangeable for gifts; POYP states that rewards are funded by advertiser spending and that prediction outcomes do not create economic gain/loss between the operator and users or among users.

Do not turn those facts into unsupported legal claims. In particular, do not state that sports betting is generally legal in Japan and do not infer legality or safety solely from the word `points`. Record the actual operation and evidence accurately. This repository context informs classification; it does not override a runtime, platform, or external policy decision.

## Architecture map

```text
src/poyto/
├── __init__.py       public exports and compatibility aliases
├── config.py         environment/settings parsing
├── token_loader.py   explicit credential-source parsing
├── token_info.py     secret-safe token/session metadata
├── session_store.py  local session persistence
├── models.py         typed data structures for sufficiently established shapes
├── exceptions.py     normalized errors
├── _http.py          HTTP transport + auth endpoints
├── _resource.py      shared resource helpers
├── resources/        route families grouped by responsibility
├── client.py         low-level mixin composition
├── auto.py           high-level token loading, persistence and refresh policy
├── cli_parser.py     argparse definitions only
├── cli_dispatch.py   command-to-client dispatch only
└── cli.py            CLI entrypoint/output handling
```

Keep responsibilities narrow. New POYP route wrappers normally belong in a matching `resources/*.py` module rather than `_http.py`, `auto.py`, or the CLI.

## Evidence model

Use these categories when changing the project:

### Observed

The real request shape is backed by direct request/response evidence. It is acceptable to document the method/path/query/body fields that are actually established.

### Observed success

A successful server response is also established. It is acceptable to type stable/useful fields from that response, while avoiding claims about unseen optional/error variants.

### Implemented / inferred

The code intentionally follows a well-supported external protocol or library convention, but exact POYP behavior is not directly established. The clearest current example is refresh-token exchange.

### Unknown

There is not enough evidence. Do not invent a route, body, header, enum, success schema, or server rule.

Whenever evidence changes, update `docs/capabilities.md` and `docs/known-gaps.md` in the same PR.

## Traffic-analysis and evidence rules

Debugging artifacts and network traces can contain production credentials and personally identifying account/device data.

Never commit or paste into source/docs/tests:

- access tokens
- refresh tokens
- Apple `id_token` values
- Apple authorization/access values
- cookies
- user IDs copied from private traffic
- stable device/vendor IDs
- email addresses or account metadata
- raw private traffic exports

Use synthetic values in tests, such as `token`, `uid`, `market-id`, and deterministic fake JWT-like strings when token shape matters.

When validating network evidence:

1. Match the exact host first (`api.poyp.app` vs `auth.poyp.app` vs unrelated Google/advertising hosts).
2. Verify HTTP method and path.
3. Record query parameters separately from JSON/form body.
4. Determine whether request body is truly absent or merely empty.
5. Check response status and content; transport failure or missing status is not proof of HTTP success.
6. Sort by timestamps when event order is ambiguous.
7. Distinguish app API calls from third-party SDK traffic.
8. Sanitize findings before committing documentation.

Do not treat a string match from an unrelated OAuth/SDK request as POYP evidence.

## Adding a new endpoint

For an established endpoint:

1. Put the wrapper in the matching resource module.
2. Preserve the exact established method/path/query/body naming.
3. Prefer keyword-only arguments for optional parameters.
4. Do not add guessed optional fields.
5. Add a MockTransport test that asserts the exact request shape.
6. Add the route to `docs/endpoints.md`.
7. Add/update the relevant capability in `docs/capabilities.md`.
8. Remove only the corresponding proven statement from `docs/known-gaps.md`.
9. Expose a CLI command only when it is broadly useful; keep library surface richer than CLI surface.

For state-changing CLI commands, require an explicit confirmation flag such as `--yes` unless there is a compelling existing convention otherwise.

## Adding response types

Most endpoint wrappers may return `Any` because the undocumented API can change.

Create a TypedDict/dataclass only when:

- a successful response is established or otherwise strongly documented
- the fields are useful to callers
- typing does not imply unsupported completeness

Do not generate huge speculative models from one payload. Prefer small types for established stable fields.

## Authentication rules

Do not weaken credential-source separation.

The high-level client deliberately avoids accidentally pairing an explicit access token with an unrelated environment/stored refresh token.

When modifying auth/session code, preserve:

- explicit credential priority
- one refresh attempt per 401 recovery path
- persistence of newly rotated refresh tokens
- masked/log-safe outputs
- local-only logout option
- distinction between established Apple login and inferred refresh exchange

Never print full secrets from CLI commands, exceptions, debug output, tests, or docs.

## Ad-reward rules

Current evidence supports:

```text
POST /api/me/ad-rewards/claim?source=watch_ad
```

with no JSON request body, plus a successful response containing:

- `earnId`
- `rewardPoints`
- `pointBalanceAfter`
- `dailyViewCount`
- `dailyViewLimit`

Do not hard-code a previously seen reward amount or daily limit as universal POYP constants.

Do not fabricate rewarded-ad SDK callbacks, completion events, provider proofs, eligibility state, or anti-abuse bypasses. The library may expose the established POYP API operation; unknown server-side qualification logic remains unknown.

## Testing policy

The default development loop is:

```bash
pip install -e '.[dev]'
pytest
ruff check .
mypy src/poyto
python scripts/code_stats.py
python -m build
```

Normal CI tests Python 3.12 (matching Docker); manually dispatch the CI workflow to test Python 3.10–3.14. Keep tests network-free by default.

Prefer `httpx.MockTransport` for API behavior. Tests for route wrappers should verify method, path, query, JSON/form body, relevant headers, and parsing of typed response fields.

Do not use live POYP credentials in CI.

## Code-size accounting

`python scripts/code_stats.py` is the canonical LOC measurement. It counts physical source lines, non-blank source lines, core vs `resources/`, test lines, and each source file individually.

If a PR significantly changes the source tree or the README/docs mention LOC, run the script and update the numeric snapshot instead of estimating.

## CLI design

Keep argparse definitions in `cli_parser.py` and behavior in `cli_dispatch.py`.

Do not move network logic into CLI modules. CLI code should call the same public client methods library users call.

Mask credentials in CLI output. State-changing commands should be visibly intentional.

## Style

Follow existing repository conventions:

- Python 3.10-compatible syntax
- `from __future__ import annotations`
- line length target 100 (Ruff `E501` intentionally ignored)
- type useful public structures without over-modeling undocumented JSON
- small resource methods
- no unnecessary dependencies; `httpx` is the core runtime dependency

## Documentation contract

When behavior changes, update documentation in the same PR.

At minimum consider `README.md`, `docs/capabilities.md`, `docs/known-gaps.md`, `docs/endpoints.md`, and topic-specific docs.

Use language such as “observed”, “established”, “implemented/inferred”, and “unknown”. Avoid “official”, “guaranteed”, or “complete API” unless that becomes independently true.

## What not to do

Do not:

- invent endpoints by naming convention
- silently turn inferred behavior into established behavior
- commit production credentials or private traffic exports
- add a broad dependency for a tiny helper
- bypass the high-level session lifecycle by duplicating auth logic in resources
- put every response into rigid models from a single sample
- make CI depend on POYP being online
- claim an unsupported feature because the raw request escape hatch could theoretically call it
- delete warnings about unofficial/undocumented API stability

## Preferred AI workflow

For nontrivial changes:

1. Read the relevant code, tests, `capabilities.md`, and `known-gaps.md`.
2. State what evidence supports the change.
3. Implement the smallest correct surface.
4. Add offline regression tests.
5. Run/verify pytest, Ruff, mypy, code stats, and build.
6. Update docs and evidence classifications.
7. Review the diff for accidental secrets or speculative claims.
8. Keep commits focused and PR descriptions explicit about established vs inferred behavior.

If evidence is missing, the correct result is often a documented gap rather than guessed code.
