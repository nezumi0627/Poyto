# syntax=docker/dockerfile:1
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    POYTO_SESSION_FILE=/data/session.json \
    POYTO_MCP_TRANSPORT=streamable-http \
    POYTO_MCP_HOST=0.0.0.0 \
    POYTO_MCP_PORT=8765

WORKDIR /app

COPY pyproject.toml README.md LICENSE ./
COPY src ./src

RUN python -m pip install --upgrade pip \
    && python -m pip install '.[agent]' \
    && groupadd --system poyto \
    && useradd --system --gid poyto --home-dir /nonexistent --shell /usr/sbin/nologin poyto \
    && mkdir -p /data \
    && chown poyto:poyto /data

USER poyto

EXPOSE 8765

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import os,socket; s=socket.create_connection(('127.0.0.1', int(os.getenv('POYTO_MCP_PORT', '8765'))), 2); s.close()"

CMD ["poyto-mcp"]
