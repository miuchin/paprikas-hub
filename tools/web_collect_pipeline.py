#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import argparse
import json
from pathlib import Path

from recipes_toolkit import load_any, normalize_recipe, dedup_recipes, write_pack


def main():
    ap = argparse.ArgumentParser(description="Build import-ready web collect pack for Paprikas Hub.")
    ap.add_argument("inputs", nargs="+", help="Input recipe files")
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--title", default="web_collect_pack")
    ap.add_argument("--source-name", default="web")
    ap.add_argument("--source-note", default="web collect pipeline")
    ap.add_argument("--against", nargs='*', default=[], help="Optional existing catalog files used only for dedup against already-known recipes")
    args = ap.parse_args()

    normalized = []
    skipped = []
    for name in args.inputs:
        for raw in load_any(Path(name)):
            rec, issues = normalize_recipe(raw, default_source_name=args.source_name, default_source_note=args.source_note)
            if rec is None:
                skipped.append({"input": name, "reason": ",".join(issues or ["invalid"])})
                continue
            if 'missing-ingredients' in issues or 'missing-steps' in issues:
                skipped.append({"input": name, "id": rec.get('id'), "naziv": rec.get('naziv'), "reason": ",".join(issues)})
                continue
            normalized.append(rec)

    base_for_compare = []
    for name in args.against:
        for raw in load_any(Path(name)):
            rec, issues = normalize_recipe(raw)
            if rec is not None and 'missing-ingredients' not in issues and 'missing-steps' not in issues:
                base_for_compare.append(rec)

    combined = base_for_compare + normalized if base_for_compare else normalized
    deduped, dedup_report = dedup_recipes(combined, fuzzy=True)
    if base_for_compare:
        base_ids = {r['id'] for r in base_for_compare}
        deduped = [r for r in deduped if r.get('id') not in base_ids]

    report = {
        "title": args.title,
        "inputs": args.inputs,
        "against": args.against,
        "normalized": len(normalized),
        "skipped": skipped[:300],
        "dedup": dedup_report,
    }
    out_dir = Path(args.out_dir)
    write_pack(out_dir, args.title, deduped, report)
    print(f"Pipeline ready: {len(deduped)} recipes -> {out_dir}")


if __name__ == '__main__':
    main()
