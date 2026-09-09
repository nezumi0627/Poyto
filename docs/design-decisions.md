# Design decisions

## MCP is an integration layer

Poyto's MCP implementation belongs under `src/poyto/mcp/` rather than alongside the HTTP/resource modules. The core client remains usable without MCP installed.

## Backward compatibility

`poyto.mcp_server` remains a small compatibility shim while the canonical implementation moves to `poyto.mcp`.

## Read-only is structural

Read-only mode does not merely ask an agent to avoid writes; mutation tools are not registered. This makes the exposed tool surface match the configured policy.

## Mutations require explicit confirmation

When mutation tools are enabled, Poyto still requires `confirm=true` for sensitive account actions. MCP annotations are metadata for the host, not the only safety mechanism.

## POYP access and host administration are separate trust boundaries

The default Poyto MCP server exposes POYP capabilities only. Generic shell execution, arbitrary filesystem editing, Docker daemon access and host-root administration are deliberately excluded. A future server-control integration should use a separate package/entrypoint and explicit authentication rather than silently expanding `poyto-mcp` authority.

## Docker defaults are conservative

The supplied container runs as an unprivileged user, stores session state under `/data`, defaults to read-only MCP and publishes only on host loopback through Compose.
