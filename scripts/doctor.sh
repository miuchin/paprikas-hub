#!/usr/bin/env bash
set -euo pipefail
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PORT="${1:-8015}"

echo "📁 ROOT: $ROOT_DIR"
echo "---- files ----"
for p in index.html server/paprikas_server.py scripts/start_paprikas_server.sh data/db/app_state.json data/db/events.ndjson docs; do
  [[ -e "$ROOT_DIR/$p" ]] && echo "✅ $p" || echo "❌ $p"
done

echo "---- port $PORT ----"
if command -v lsof >/dev/null 2>&1; then
  lsof -nP -iTCP:"$PORT" -sTCP:LISTEN || echo "(nema listenera na $PORT)"
elif command -v ss >/dev/null 2>&1; then
  ss -ltnp "sport = :$PORT" || true
fi

echo "---- endpoint probes (ako FULL server radi) ----"
if command -v curl >/dev/null 2>&1; then
  for u in "http://127.0.0.1:${PORT}/api/ping" "http://127.0.0.1:${PORT}/api/db"; do
    code=$(curl -s -o /dev/null -w "%{http_code}" "$u" || true)
    echo "$code  $u"
  done
  echo "Napomena: 404/501 = static http.server; 200 = full Paprikas server."
else
  echo "curl nije instaliran."
fi
