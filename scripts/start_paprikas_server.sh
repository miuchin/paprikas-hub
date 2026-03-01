#!/usr/bin/env bash
set -euo pipefail
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"
PORT="${1:-${PAPRIKAS_PORT:-8015}}"
HOST="${PAPRIKAS_HOST:-0.0.0.0}"

port_in_use(){
  if command -v ss >/dev/null 2>&1; then
    ss -ltn "sport = :$1" | tail -n +2 | grep -q . && return 0 || return 1
  elif command -v lsof >/dev/null 2>&1; then
    lsof -iTCP:"$1" -sTCP:LISTEN >/dev/null 2>&1 && return 0 || return 1
  fi
  return 1
}

show_port_owner(){
  local p="$1"
  if command -v lsof >/dev/null 2>&1; then
    echo "ℹ️  Proces na portu $p:"
    lsof -nP -iTCP:"$p" -sTCP:LISTEN || true
  elif command -v ss >/dev/null 2>&1; then
    echo "ℹ️  Port $p je zauzet (ss):"
    ss -ltnp "sport = :$p" || true
  fi
}

if port_in_use "$PORT"; then
  echo "❌ Port $PORT je već zauzet (verovatno radi python -m http.server)."
  show_port_owner "$PORT"
  echo ""
  echo "Rešenje A (preporučeno): zaustavi static server pa pokreni full server na istom portu:"
  echo "  Ctrl+C u terminalu gde radi http.server"
  echo "  ./scripts/start_paprikas_server.sh $PORT"
  echo ""
  echo "Rešenje B: pokreni full server na drugom portu (npr. 8016):"
  echo "  ./scripts/start_paprikas_server.sh 8016"
  echo "  i otvori: http://127.0.0.1:8016/"
  exit 98
fi

echo "🚀 Pokrećem Paprikas Hub FULL server na ${HOST}:${PORT}"
exec python3 server/paprikas_server.py --host "$HOST" --port "$PORT"
