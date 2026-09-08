# Reverse-engineering notes

Poyto documents client/server behavior conservatively and avoids inventing undocumented behavior.

## Method

1. Collect authorized request/response evidence from the user's own session.
2. Group requests by host and normalized path.
3. Compare repeated requests to separate stable fields from per-session IDs.
4. Record method, query, JSON body, authentication style, and relevant `x-poyp-*` headers.
5. Add a dedicated client method only when a request shape is sufficiently established.
6. Add mock tests that assert the generated request matches the established shape.

## Safety rules used by this repository

- Raw private traffic exports are never committed.
- User bearer tokens, refresh tokens, Apple tokens, cookies, and device identifiers are never copied into source.
- Unknown operations stay unknown; the generic request helper exists for research without pretending an endpoint is stable.
- State-changing CLI commands require `--yes`.

## Updating from new evidence

Compare new evidence with `docs/endpoints.md`, update only verified differences, then add or adjust mock tests before merging.
