#!/usr/bin/env bash
set -euo pipefail
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
chmod +x "$ROOT_DIR/scripts/"*.sh 2>/dev/null || true
exec "$ROOT_DIR/scripts/setup_paprikas_hub_manjaro.sh"
