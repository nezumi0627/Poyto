# Changelog

All notable Poyto changes are recorded here.

## Unreleased

- Added multi-architecture Docker publication for native `linux/amd64` and `linux/arm64` GitHub runners.
- Added standalone Poyto Server Control for ChatGPT/custom MCP clients, combining Poyto tools with Codex/Chat On Steroids Core-inspired `read`, `apply_patch`, `exec_command`, and `write_stdin` primitives without a Chat On Steroids runtime dependency.
- Added independent Bearer authentication for the control plugin and persistent token storage.
- Added a loopback-only Docker overlay for direct ChatGPT Secure MCP Tunnel deployment without a Chat On Steroids intermediary.
- Added an explicit opt-in Docker host-control overlay using host PID namespace, writable host-root mount, and `nsenter`; normal Docker mode remains unprivileged/container-scoped.
- Kept Android/ADB/Frida as development-time API verification only; production Docker operation does not depend on an Android device.

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
