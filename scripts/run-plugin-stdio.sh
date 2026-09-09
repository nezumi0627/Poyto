#!/usr/bin/env bash
set -euo pipefail

# A stable absolute command for tunnel-client and local plugin hosts.
poyto_repo=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)
export PATH="$poyto_repo/.venv/bin:$PATH"
export POYTO_PLUGIN_ROOTS="${POYTO_PLUGIN_ROOTS:-$poyto_repo}"
if [[ ! -x "$poyto_repo/.venv/bin/poyto-plugin" ]]; then
  echo "Install first: python3 -m venv .venv && .venv/bin/pip install -e '.[agent]'" >&2
  exit 1
fi
exec "$poyto_repo/.venv/bin/poyto-plugin" --transport stdio
