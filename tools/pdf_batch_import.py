#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Batch import recipes from single-recipe PDFs into data/recipes/*.json + update index.

For cookbook-style PDFs with many recipes use:
  python3 tools/pdf_cookbook_import_pack.py input.pdf --out-dir data/import_ready/my_pack --layout carobna
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from datetime import datetime, timezone
import importlib.util

PROJECT_ROOT = Path(__file__).resolve().parent.parent
SERVER_PY = PROJECT_ROOT / 'server' / 'paprikas_server.py'
RECIPES_DIR = PROJECT_ROOT / 'data' / 'recipes'
INDEX_JSON = RECIPES_DIR / 'index.json'


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace('+00:00','Z')


def load_server_module():
    spec = importlib.util.spec_from_file_location('paprikas_server', str(SERVER_PY))
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(mod)
    return mod


def safe_write_json(path: Path, obj: dict) -> None:
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2) + "\n", encoding='utf-8')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('pdf_dir', help='Folder that contains PDF files (one PDF = one recipe)')
    ap.add_argument('--dry-run', action='store_true')
    ap.add_argument('--limit', type=int, default=0)
    args = ap.parse_args()

    pdf_dir = Path(args.pdf_dir).expanduser().resolve()
    if not pdf_dir.exists() or not pdf_dir.is_dir():
        raise SystemExit(f'Not a folder: {pdf_dir}')

    mod = load_server_module()
    idx = {"version":"recipes-index-v1", "updated_utc": utc_now(), "recipes":[]}
    if INDEX_JSON.exists():
        try:
            idx = json.loads(INDEX_JSON.read_text(encoding='utf-8'))
        except Exception:
            pass
    idx.setdefault('recipes', [])
    existing_ids = {r.get('id') for r in idx['recipes'] if isinstance(r, dict) and r.get('id')}

    pdfs = sorted(pdf_dir.glob('*.pdf'))
    if args.limit and args.limit > 0:
        pdfs = pdfs[:args.limit]
    if not pdfs:
        raise SystemExit('No *.pdf files found in folder.')

    added = 0
    for pdf in pdfs:
        try:
            recipe, warnings = mod.recipe_from_pdf_bytes(pdf.read_bytes())
            rid = str(recipe.get('id') or '')
            if not rid:
                print(f'[SKIP] {pdf.name}: missing id')
                continue
            base = rid
            n = 2
            while rid in existing_ids:
                rid = f'{base}_{n}'
                n += 1
            recipe['id'] = rid
            recipe.pop('user', None)
            recipe['created_utc'] = utc_now()
            recipe['updated_utc'] = recipe['created_utc']
            recipe.setdefault('izvor', {})
            recipe['izvor']['naziv'] = recipe['izvor'].get('naziv') or 'PDF batch import'
            recipe['izvor']['napomena'] = recipe['izvor'].get('napomena') or f'Imported from: {pdf.name}'
            filename = f'{rid}.json'
            print(f'[OK] {pdf.name} -> {filename}')
            for w in warnings[:6]:
                print(f'  - note: {w}')
            if not args.dry_run:
                safe_write_json(RECIPES_DIR / filename, recipe)
                idx['recipes'].append({
                    'id': rid,
                    'file': filename,
                    'naziv': recipe.get('naziv',''),
                    'tags': recipe.get('tags',[]),
                    'kategorija': recipe.get('kategorija',[]),
                    'vreme_min': recipe.get('vreme_min',0),
                    'porcije': recipe.get('porcije',0),
                })
                existing_ids.add(rid)
            added += 1
        except Exception as e:
            print(f'[FAIL] {pdf.name}: {e}')

    if not args.dry_run:
        idx['updated_utc'] = utc_now()
        idx['recipes'] = sorted(idx['recipes'], key=lambda x: str(x.get('naziv','')).lower())
        safe_write_json(INDEX_JSON, idx)

    print(f'\nDone. Processed={len(pdfs)} Added={added} DryRun={args.dry_run}')


if __name__ == '__main__':
    main()
