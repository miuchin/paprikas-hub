#!/usr/bin/env bash
set -euo pipefail

PORT="${1:-8015}"
HOST="${PAPRIKAS_HOST:-0.0.0.0}"

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT_DIR"

PY="${PYTHON_BIN:-python3}"

# Create venv if missing
if [ ! -d ".venv" ]; then
  echo "🧪 Kreiram virtualenv (.venv)"
  "$PY" -m venv .venv
fi

# Activate
# shellcheck disable=SC1091
source .venv/bin/activate

echo "⬇️  Instaliram dependencies (requirements.txt)"
python -m pip install --upgrade pip
python -m pip install -r requirements.txt

echo "🚀 Pokrećem Paprikas Hub server na http://127.0.0.1:${PORT}/"
exec python server/paprikas_server.py --host "$HOST" --port "$PORT"
