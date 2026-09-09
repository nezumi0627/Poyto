# MCP architecture

The MCP adapter is intentionally thin:

```text
MCP host
  ↓
poyto.mcp.server
  ↓
PoytoClient
  ↓
resource mixins
  ↓
POYP HTTP API
```

This keeps transport/agent concerns out of the core API implementation and makes future MCP transports or hosts replaceable without changing resource code.
