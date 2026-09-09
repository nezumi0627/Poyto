# syntax=docker/dockerfile:1
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    POYTO_SESSION_FILE=/data/session.json \
    POYTO_PLUGIN_HOST=0.0.0.0 \
    POYTO_PLUGIN_PORT=8765 \
    POYTO_PLUGIN_TOKEN_FILE=/data/control-plugin.token \
    POYTO_PLUGIN_ROOTS=/workspace:/data \
    POYTO_PLUGIN_EXEC_MODE=container

WORKDIR /app

COPY pyproject.toml README.md LICENSE ./
COPY src ./src

RUN DEBIAN_FRONTEND=noninteractive apt-get update \
    && apt-get install -y --no-install-recommends bash git procps ripgrep util-linux \
    && rm -rf /var/lib/apt/lists/* \
    && python -m pip install --upgrade pip \
    && python -m pip install '.[agent]' \
    && groupadd --gid 10001 poyto \
    && useradd --uid 10001 --gid 10001 --no-create-home --home-dir /nonexistent --shell /usr/sbin/nologin poyto \
    && mkdir -p /data /workspace \
    && chown -R poyto:poyto /data /workspace

USER poyto

EXPOSE 8765

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import os,socket; s=socket.create_connection(('127.0.0.1', int(os.getenv('POYTO_PLUGIN_PORT', '8765'))), 2); s.close()"

CMD ["poyto-plugin"]
