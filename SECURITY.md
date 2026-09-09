# Security

Poyto handles authentication material and can perform account-changing actions, so credentials and remote-control surfaces must be treated as sensitive.

## Never commit

- POYP access or refresh tokens
- Apple identity/access tokens or nonces
- cookies
- raw private traffic exports or HAR captures
- session JSON files
- `.env` files
- tunnel/API credentials
- stable device/vendor identifiers copied from real sessions

The repository `.gitignore` blocks common secret-bearing files, but review every commit before pushing.

## MCP

The default `poyto-mcp` server exposes POYP operations only. It does not expose a generic shell, arbitrary filesystem editor, Docker socket, host PID namespace, or host-root mount.

For remote/research use, prefer `--read-only`; mutation tools are then omitted entirely. Outside read-only mode, state-changing tools still require explicit `confirm=true`.

`stdio` is the safest default because the MCP host owns the local process pipes. For Streamable HTTP, bind to loopback (`127.0.0.1`) unless the endpoint is behind an appropriate private/authenticated transport. Do not publish an unauthenticated mutation-capable MCP endpoint directly to the Internet.

The included Docker Compose configuration publishes MCP only on host loopback and defaults to read-only mode. Expanding Poyto into generic server administration should use a separate package/entrypoint and separate authentication boundary rather than widening the default MCP server.

## Reporting a security issue

Please avoid filing public issues that contain working credentials, private traffic exports, private account data, tunnel credentials, or reproducible secrets. Revoke or rotate any credential that may have been exposed.

## Scope

This is an unofficial client. It does not attempt to bypass POYP authorization controls; requests are made using credentials supplied by the authorized account user.
