#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

from recipes_toolkit import dedup_recipes, normalize_recipe

PROJECT_ROOT = Path(__file__).resolve().parent.parent
RECIPES_DIR = PROJECT_ROOT / 'data' / 'recipes'
CHUNKS_DIR = PROJECT_ROOT / 'data' / 'recipes_chunks'
APP_STATE = PROJECT_ROOT / 'data' / 'db' / 'app_state.json'


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace('+00:00','Z')


def load_base_recipes() -> list[dict]:
    out = []
    for f in sorted(RECIPES_DIR.glob('*.json')):
        if f.name == 'index.json':
            continue
        try:
            out.append(json.loads(f.read_text(encoding='utf-8')))
        except Exception:
            continue
    return out


def load_user_recipes() -> list[dict]:
    try:
        payload = json.loads(APP_STATE.read_text(encoding='utf-8'))
        raw = payload.get('data', {}).get('paprikasHubRecipesUserV1', '[]')
        arr = json.loads(raw)
        return arr if isinstance(arr, list) else []
    except Exception:
        return []


def main():
    ap = argparse.ArgumentParser(description='Merge recipe catalog and build chunk files.')
    ap.add_argument('--part-size', type=int, default=200)
    ap.add_argument('--clear-user-db', action='store_true')
    args = ap.parse_args()

    base = load_base_recipes()
    user = load_user_recipes()
    normalized = []
    for raw in base + user:
        rec, issues = normalize_recipe(raw, default_source_name='katalog', default_source_note='merged catalog')
        if rec is None:
            continue
        rec['user'] = False
        normalized.append(rec)
    final, report = dedup_recipes(normalized, fuzzy=False)

    CHUNKS_DIR.mkdir(parents=True, exist_ok=True)
    for old in CHUNKS_DIR.glob('recipes-part-*.json'):
        old.unlink()
    parts = []
    for i in range(0, len(final), args.part_size):
        chunk = final[i:i+args.part_size]
        file = f'recipes-part-{(i//args.part_size)+1:03d}.json'
        payload = {'part': (i//args.part_size)+1, 'count': len(chunk), 'recipes': chunk}
        (CHUNKS_DIR / file).write_text(json.dumps(payload, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
        parts.append({'file': file, 'count': len(chunk)})
    manifest = {
        'version': 'recipes-chunks-v1',
        'generated_utc': utc_now(),
        'count': len(final),
        'part_size': args.part_size,
        'parts': parts,
        'source_counts': {'base_files': len(base), 'user_db': len(user)},
        'dedup_report': {'total_in': report.get('total_in'), 'total_out': report.get('total_out')},
    }
    (CHUNKS_DIR / 'manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')

    build_report = {'generated_utc': utc_now(), 'base_loaded': len(base), 'user_loaded': len(user), 'final_count': len(final), 'chunks': len(parts), 'part_size': args.part_size}
    (PROJECT_ROOT / 'data' / 'exports').mkdir(parents=True, exist_ok=True)
    (PROJECT_ROOT / 'data' / 'exports' / 'BUILD_REPORT_v5_12_7.json').write_text(json.dumps(build_report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')

    if args.clear_user_db and APP_STATE.exists():
        payload = json.loads(APP_STATE.read_text(encoding='utf-8'))
        payload.setdefault('data', {})['paprikasHubRecipesUserV1'] = '[]'
        payload['meta'] = payload.get('meta', {})
        payload['meta']['updated_utc'] = utc_now()
        APP_STATE.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')

    print(f'Chunk catalog ready: {len(final)} recipes / {len(parts)} parts -> {CHUNKS_DIR}')


if __name__ == '__main__':
    main()
