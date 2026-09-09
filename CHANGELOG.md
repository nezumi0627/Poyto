# Changelog

All notable Poyto changes are recorded here.

## Unreleased

- Refactored MCP support into the dedicated `poyto.mcp` package while preserving the legacy `poyto.mcp_server` import path.
- Added explicit read-only MCP mode and MCP tool annotations for safer agent/remote use.
- Added first-class MCP and Docker documentation.
- Added a minimal unprivileged Docker image and loopback-only Compose setup for read-only MCP deployment.
- Kept generic shell/filesystem/host-root control outside the default Poyto MCP trust boundary.

## 0.1.0 — 2026-09-08

Initial public client built from the supplied POYP HAR captures.

- Added Apple/Supabase authentication and token refresh
- Added account, balance, portfolio, mission, notification, referral, market, ranking and discovery APIs
- Added observed buy and sell request shapes
- Added comment create/reply/edit/delete/like
- Added follow/unfollow and public user history APIs
- Added market activity, charts, asset price and balance transactions
- Added CLI with `--yes` protection for state-changing actions
- Added typed package metadata, tests, CI, documentation, examples and security guidance
