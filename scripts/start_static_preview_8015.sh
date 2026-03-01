#!/usr/bin/env bash
set -euo pipefail
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"
PORT="${1:-8015}"
echo "ℹ️  Pokrenut je STATIC preview (python -m http.server)."
echo "   UI radi na http://127.0.0.1:${PORT}/index.html?static=1"
echo "   API /api/db NE POSTOJI u ovom modu (404 je očekivano)."
echo "   Savet: koristi ?static=1 da UI ne pokušava API probe."
exec python3 -m http.server "$PORT"
