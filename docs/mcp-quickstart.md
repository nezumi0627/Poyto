# MCP quickstart

```bash
git clone https://github.com/nezumi0627/Poyto.git
cd Poyto
python -m venv .venv
pip install -e '.[agent]'
poyto-mcp
```

The default transport is local `stdio`.

For a local read-only HTTP endpoint:

```bash
poyto-mcp --transport streamable-http --host 127.0.0.1 --port 8765 --read-only
```

For Docker:

```bash
docker compose up -d --build
```

Then connect an MCP-capable host through an appropriate local/private transport. Keep Poyto credentials on the machine running Poyto; do not paste them into chat.
