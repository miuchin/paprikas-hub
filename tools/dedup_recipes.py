#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import argparse
import json
from pathlib import Path

from recipes_toolkit import load_any, normalize_recipe, dedup_recipes, to_wrapped_payload


def main():
    ap = argparse.ArgumentParser(description="Deduplicate Paprikas Hub recipe batches.")
    ap.add_argument("inputs", nargs="+", help="Input files (JSON/NDJSON/CSV/TXT)")
    ap.add_argument("--out", required=True)
    ap.add_argument("--format", choices=["wrapped", "json", "ndjson"], default="wrapped")
    ap.add_argument("--no-fuzzy", action="store_true")
    args = ap.parse_args()

    all_recipes = []
    invalid = 0
    for name in args.inputs:
        for raw in load_any(Path(name)):
            rec, issues = normalize_recipe(raw)
            if rec is None or 'missing-ingredients' in issues or 'missing-steps' in issues:
                invalid += 1
                continue
            all_recipes.append(rec)

    deduped, report = dedup_recipes(all_recipes, fuzzy=not args.no_fuzzy)
    report["invalid_skipped"] = invalid
    outp = Path(args.out)
    if args.format == 'json':
        outp.write_text(json.dumps(deduped, ensure_ascii=False, indent=2) + "\n", encoding='utf-8')
    elif args.format == 'ndjson':
        with outp.open('w', encoding='utf-8') as f:
            for r in deduped:
                f.write(json.dumps(r, ensure_ascii=False) + "\n")
    else:
        outp.write_text(json.dumps(to_wrapped_payload(deduped), ensure_ascii=False, indent=2) + "\n", encoding='utf-8')
    report_path = outp.with_name(outp.stem + '_dedup_report.json')
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding='utf-8')
    print(f"Dedup done: {len(all_recipes)} -> {len(deduped)} | skipped invalid: {invalid} | report: {report_path} | wrote {outp}")


if __name__ == '__main__':
    main()
