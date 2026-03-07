#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Build JNA 'Top Clean' import pack for Paprikas Hub.

Input: data/catalog/bridges/jna_ocr_review_export_v5.13.9.json
Output:
  - data/catalog/imports/jna_top_clean_import_<VERSION>.json
  - data/catalog/imports/jna_top_clean_import_<VERSION>.ndjson
  - data/catalog/imports/jna_top_clean_summary_<VERSION>.json

This pack is meant to be SAFE for Recipe Atlas import:
- It does NOT attempt to parse OCR ingredient tables.
- It creates minimal recipe stubs (title + category guess + notes + source refs).
- User can later enrich ingredients/steps.

Run:
  python3 tools/build_jna_top_clean_import.py --version v5.15.0 --limit 31
"""

from __future__ import annotations

import argparse
import json
import re
from datetime import datetime, timezone
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent
REVIEW_EXPORT = PROJECT_ROOT / "data" / "catalog" / "bridges" / "jna_ocr_review_export_v5.13.9.json"
OUT_DIR = PROJECT_ROOT / "data" / "catalog" / "imports"


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def slugify(s: str) -> str:
    s = (s or "").strip().lower()
    # keep serbian letters, then map
    rep = {
        "š":"s","đ":"dj","č":"c","ć":"c","ž":"z",
    }
    for k, v in rep.items():
        s = s.replace(k, v)
    s = re.sub(r"\s+", " ", s)
    s = re.sub(r"[^a-z0-9 ]+", " ", s)
    s = re.sub(r"\s+", "_", s).strip("_")
    return (s[:64] if s else "jna_item")


def guess_categories(cat: str) -> list[str]:
    c = (cat or "").strip().lower()
    if not c:
        return []
    # Keep original guess but normalize some common ones
    mapping = {
        "napici": ["napici"],
        "supa": ["supa"],
        "corbe": ["supa"],
        "jelo_od_mesa": ["glavno"],
        "jelo_od_ribe": ["glavno", "riba"],
        "salate": ["salata"],
        "poslastice": ["desert"],
        "peciva": ["pecivo"],
        "prilozi": ["prilog"],
        "zimnica": ["zimnica"],
    }
    return mapping.get(c, [c])


def make_recipe_stub(cand: dict, version: str) -> dict:
    title = str(cand.get("naziv") or "").strip()
    rid = cand.get("id") or f"jna_{slugify(title)}"
    page = cand.get("page_start")
    preview = str(cand.get("preview") or "").strip()
    cat = cand.get("category_guess") or ""
    issues = cand.get("issues") or []
    src = cand.get("source_refs") or {}

    notes = []
    if page is not None:
        notes.append(f"JNA OCR izvor: str. {page}.")
    if cat:
        notes.append(f"Kategorija (OCR guess): {cat}.")
    notes.append("⚠️ Ovo je 'clean stub' (bez auto-parsiranja tabela/gramaža iz OCR-a). Dopluni sastojke i korake ručno.")
    if preview:
        notes.append("OCR preview (kontrolno): " + preview[:500])
    if issues:
        notes.append("Issues: " + ", ".join([str(x) for x in issues]))

    return {
        "id": str(rid),
        "naziv": title,
        "kategorija": guess_categories(str(cat)),
        "tags": ["jna", "ocr", "top_clean", "review_to_atlas"],
        "porcije": 0,
        "vreme_min": 0,
        "tezina": "lako",
        "sastojci": [],
        "koraci": [],
        "napomene": "\n".join(notes).strip(),
        "izvor": {
            "naziv": "Kuvar JNA (OCR bundle)",
            "napomena": f"Top Clean import pack {version}",
            "url": ""
        },
        "user": True,
        "source_refs": src,
        "updated_utc": utc_now(),
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--version", default="v5.15.0")
    ap.add_argument("--limit", type=int, default=31)
    args = ap.parse_args()

    if not REVIEW_EXPORT.exists():
        raise SystemExit(f"Missing input: {REVIEW_EXPORT}")

    OUT_DIR.mkdir(parents=True, exist_ok=True)

    obj = json.loads(REVIEW_EXPORT.read_text(encoding="utf-8"))
    safe = obj.get("safe_preview_candidates") or []
    review = obj.get("review_only_candidates") or []
    # prefer safe preview, then fill from review if needed
    pool = list(safe) + list(review)

    stubs = []
    seen = set()
    for cand in pool:
        cid = str(cand.get("id") or "")
        if not cid or cid in seen:
            continue
        title = str(cand.get("naziv") or "").strip()
        if not title:
            continue
        seen.add(cid)
        stubs.append(make_recipe_stub(cand, args.version))
        if len(stubs) >= args.limit:
            break

    pack = {
        "schema": "paprikas-hub-jna-clean-pack-v1",
        "version": args.version,
        "created_utc": utc_now(),
        "source_review_export": str(REVIEW_EXPORT.relative_to(PROJECT_ROOT)).replace('\\','/'),
        "limit": args.limit,
        "recipes": stubs,
    }

    out_json = OUT_DIR / f"jna_top_clean_import_{args.version}.json"
    out_ndjson = OUT_DIR / f"jna_top_clean_import_{args.version}.ndjson"
    out_summary = OUT_DIR / f"jna_top_clean_summary_{args.version}.json"

    out_json.write_text(json.dumps(pack, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    out_ndjson.write_text("\n".join(json.dumps(r, ensure_ascii=False) for r in stubs) + "\n", encoding="utf-8")

    summary = {
        "schema": pack["schema"],
        "version": pack["version"],
        "created_utc": pack["created_utc"],
        "count": len(stubs),
        "first_ids": [r["id"] for r in stubs[:10]],
        "out_json": str(out_json.relative_to(PROJECT_ROOT)).replace('\\','/'),
        "out_ndjson": str(out_ndjson.relative_to(PROJECT_ROOT)).replace('\\','/'),
    }
    out_summary.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    print(f"OK: {len(stubs)} recipes -> {out_json}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
