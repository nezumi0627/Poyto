# MCP security notes

Use `stdio` for local hosts when possible. For network transports, keep the listener on loopback or behind a private/authenticated transport.

`--read-only` removes mutation tools from the server instead of relying on prompt instructions. When mutation tools are enabled, Poyto still requires explicit `confirm=true` for sensitive account changes.

Poyto authentication and MCP transport authentication are separate concerns. A valid POYP session authorizes API requests; it does not authenticate arbitrary network callers to an MCP endpoint.

The default MCP server intentionally has no generic shell/filesystem/host-root tools.
