#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import argparse
import json
from pathlib import Path

from recipes_toolkit import load_any, normalize_recipe, dedup_recipes, to_wrapped_payload


def main():
    ap = argparse.ArgumentParser(description="Validate and normalize web/batch recipes for Paprikas Hub.")
    ap.add_argument("inputs", nargs="+", help="JSON/NDJSON/CSV/TXT inputs")
    ap.add_argument("--out", required=True, help="Output file (.json/.ndjson/.wrapped.json)")
    ap.add_argument("--format", choices=["wrapped", "json", "ndjson"], default="wrapped")
    ap.add_argument("--source-name", default="web")
    ap.add_argument("--source-note", default="validated web collect")
    ap.add_argument("--no-dedup", action="store_true")
    args = ap.parse_args()

    cleaned = []
    skipped = []
    issues_summary = {}
    for name in args.inputs:
        for obj in load_any(Path(name)):
            rec, issues = normalize_recipe(obj, default_source_name=args.source_name, default_source_note=args.source_note)
            if rec is None:
                skipped.append({"input": name, "reason": ",".join(issues or ["invalid"])})
                continue
            if "missing-ingredients" in issues or "missing-steps" in issues:
                skipped.append({"input": name, "id": rec.get("id"), "naziv": rec.get("naziv"), "reason": ",".join(issues)})
                continue
            cleaned.append(rec)
            for issue in issues:
                issues_summary[issue] = issues_summary.get(issue, 0) + 1

    report = {"inputs": args.inputs, "validated_before_dedup": len(cleaned), "skipped": skipped[:300], "issues": issues_summary}
    if args.no_dedup:
        deduped = cleaned
        report["dedup"] = {"disabled": True}
    else:
        deduped, dedup_report = dedup_recipes(cleaned, fuzzy=True)
        report["dedup"] = dedup_report

    outp = Path(args.out)
    if args.format == 'json':
        outp.write_text(json.dumps(deduped, ensure_ascii=False, indent=2) + "\n", encoding='utf-8')
    elif args.format == 'ndjson':
        with outp.open('w', encoding='utf-8') as f:
            for r in deduped:
                f.write(json.dumps(r, ensure_ascii=False) + "\n")
    else:
        outp.write_text(json.dumps(to_wrapped_payload(deduped), ensure_ascii=False, indent=2) + "\n", encoding='utf-8')

    report["validated_after_dedup"] = len(deduped)
    report_path = outp.with_name(outp.stem + '_report.json')
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding='utf-8')
    print(f"Validated: {len(deduped)} | skipped: {len(skipped)} | report: {report_path} | wrote {outp}")


if __name__ == "__main__":
    main()
