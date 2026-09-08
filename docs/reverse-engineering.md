# Reverse-engineering notes

Poyto is built from traffic captured from the user's own POYP session. The goal is to document observed client/server behavior without inventing undocumented behavior.

## Method

1. Capture app traffic in HAR format.
2. Group requests by host and normalized path.
3. Compare repeated requests to separate stable fields from per-session IDs.
4. Record method, query, JSON body, authentication style, and relevant `x-poyp-*` headers.
5. Add a dedicated client method only when a request shape has actually been observed.
6. Add mock tests that assert the generated request matches the observed shape.

## Safety rules used by this repository

- HAR files are never committed.
- User bearer tokens, refresh tokens, Apple tokens, cookies, and device identifiers are never copied into source.
- Unknown operations stay unknown; the generic request helper exists for research without pretending an endpoint is stable.
- State-changing CLI commands require `--yes`.

## Updating from a new HAR

Compare the new capture with `docs/endpoints.md`, update only confirmed differences, then add or adjust mock tests before merging.
