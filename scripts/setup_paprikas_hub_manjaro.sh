#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="/home/miuchins/Desktop/SINET/paprikas-Hub"
PACKAGE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
STAMP="$(date +%Y%m%d-%H%M%S)"

echo "📦 Package dir: $PACKAGE_DIR"
echo "🎯 Target root: $PROJECT_ROOT"

# Safety check: run from extracted package root (or installed root)
if [[ ! -f "$PACKAGE_DIR/index.html" ]] || [[ ! -d "$PACKAGE_DIR/scripts" ]] || [[ ! -d "$PACKAGE_DIR/server" ]]; then
  echo "❌ Ne deluje da si u root folderu paketa (fale index.html/scripts/server)."
  echo "   Raspakuj ZIP pa pokreni ovu skriptu iz tog foldera."
  exit 1
fi

mkdir -p "$PROJECT_ROOT"

# If package dir is already the target root, do in-place setup only
if [[ "$PACKAGE_DIR" == "$PROJECT_ROOT" ]]; then
  echo "ℹ️  Paket je već u target root folderu. Radim in-place setup (bez kopiranja istih fajlova)."
  mkdir -p "$PROJECT_ROOT"/{data/db/backups,data/catalog/modules,data/exports,server,scripts,docs,logs}
  [[ -f "$PROJECT_ROOT/data/db/app_state.json" ]] || cp -f "$PACKAGE_DIR/data/db/app_state.json" "$PROJECT_ROOT/data/db/app_state.json"
  [[ -f "$PROJECT_ROOT/data/db/events.ndjson" ]] || : > "$PROJECT_ROOT/data/db/events.ndjson"
  chmod +x "$PROJECT_ROOT"/scripts/*.sh 2>/dev/null || true
  chmod +x "$PROJECT_ROOT"/server/*.py 2>/dev/null || true
  echo "✅ In-place setup završen: $PROJECT_ROOT"
  echo "➡️  FULL server:  cd '$PROJECT_ROOT' && ./scripts/start_paprikas_server.sh"
  echo "➡️  STATIC:       cd '$PROJECT_ROOT' && ./scripts/start_static_preview_8015.sh"
  exit 0
fi
mkdir -p "$PROJECT_ROOT"/{data/db/backups,data/catalog/modules,data/exports,server,scripts,docs,logs}

if [[ -f "$PROJECT_ROOT/index.html" ]]; then
  cp -f "$PROJECT_ROOT/index.html" "$PROJECT_ROOT/index.backup-$STAMP.html"
fi

# Core runtime files (root)
for f in index.html README.md; do
  [[ -f "$PACKAGE_DIR/$f" ]] && cp -f "$PACKAGE_DIR/$f" "$PROJECT_ROOT/$f"
done

# Runtime dirs (merge)
cp -rf "$PACKAGE_DIR/server/." "$PROJECT_ROOT/server/"
cp -rf "$PACKAGE_DIR/scripts/." "$PROJECT_ROOT/scripts/"
cp -rf "$PACKAGE_DIR/docs/." "$PROJECT_ROOT/docs/"

# Optional catalog templates
if [[ -d "$PACKAGE_DIR/data/catalog" ]]; then
  cp -rf "$PACKAGE_DIR/data/catalog/." "$PROJECT_ROOT/data/catalog/"
fi

# DB skeleton only if missing (do not overwrite user data)
if [[ ! -f "$PROJECT_ROOT/data/db/app_state.json" ]] && [[ -f "$PACKAGE_DIR/data/db/app_state.json" ]]; then
  cp -f "$PACKAGE_DIR/data/db/app_state.json" "$PROJECT_ROOT/data/db/app_state.json"
fi
[[ -f "$PROJECT_ROOT/data/db/events.ndjson" ]] || : > "$PROJECT_ROOT/data/db/events.ndjson"

# Keep placeholders if absent
[[ -d "$PROJECT_ROOT/data/db/backups" ]] || mkdir -p "$PROJECT_ROOT/data/db/backups"
[[ -d "$PROJECT_ROOT/data/exports" ]] || mkdir -p "$PROJECT_ROOT/data/exports"
[[ -d "$PROJECT_ROOT/logs" ]] || mkdir -p "$PROJECT_ROOT/logs"

chmod +x "$PROJECT_ROOT"/scripts/*.sh 2>/dev/null || true
chmod +x "$PROJECT_ROOT"/server/*.py 2>/dev/null || true

echo ""
echo "✅ Paprikas Hub setup završen"
echo "📁 Root: $PROJECT_ROOT"
echo ""
echo "➡️  FULL server (UI + API + JSON DB):"
echo "   cd '$PROJECT_ROOT' && ./scripts/start_paprikas_server.sh"
echo ""
echo "➡️  Static preview only (bez API):"
echo "   cd '$PROJECT_ROOT' && ./scripts/start_static_preview_8015.sh"
echo ""
echo "🧪 Test API:"
echo "   http://127.0.0.1:8015/api/ping"
echo "   http://127.0.0.1:8015/api/db"
