#!/usr/bin/env bash
set -euo pipefail
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DB_FILE="$ROOT_DIR/data/db/app_state.json"
BACKUP_DIR="$ROOT_DIR/data/db/backups"
mkdir -p "$BACKUP_DIR"
STAMP="$(date +%Y%m%d-%H%M%S)"
cp -f "$DB_FILE" "$BACKUP_DIR/app_state-$STAMP.json"
echo "✅ Backup: $BACKUP_DIR/app_state-$STAMP.json"
