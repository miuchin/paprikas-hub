#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import argparse
import io
import json
import re
from pathlib import Path

import pdfplumber

from recipes_toolkit import normalize_ingredient_line, looks_like_nutri_or_sidebar, split_steps, slugify, write_pack

ING_HEADINGS = [r"\bsastojci\b", r"\bpotrebno je\b", r"\bza testo\b", r"\bza fil\b"]
STEP_HEADINGS = [r"\bpriprema\b", r"\bnačin pripreme\b", r"\bnacin pripreme\b", r"\bkako se priprema\b", r"\bpostupak\b"]
NON_TITLE = [r"^strana\s+\d+", r"^page\s+\d+", r"^sadržaj$", r"^sadrzaj$", r"^predgovor$", r"^uvod$", r"^napomena$"]
QTY_RE = re.compile(r"^((?:oko\s+)?\d+[\d\s\.,/xX-]*\s*(?:kg|g|gr|mg|ml|l|dl|cl|kašike|kašika|kasike|kasika|šolje|solje|šolja|solja|kom|komada|lista|veze|veza|glavice|glavica|čena|čen[a-zčćšđž]+|pakovanja|pakovanje|prstohvat[a-zčćšđž]*))\s+(.+)$", re.I)


def extract_pdf_pages(pdf_path: Path, page_from: int = 1, page_to: int | None = None, max_pages: int = 0) -> list[tuple[int, str]]:
    pages = []
    with pdfplumber.open(str(pdf_path)) as pdf:
        total = len(pdf.pages)
        start = max(page_from, 1)
        end = page_to if page_to else total
        for idx in range(start-1, min(end, total)):
            if max_pages and len(pages) >= max_pages:
                break
            text = pdf.pages[idx].extract_text() or ""
            pages.append((idx+1, text))
    return pages


def normalize_lines(text: str) -> list[str]:
    lines = []
    for raw in text.splitlines():
        ln = raw.replace('\xa0', ' ')
        ln = re.sub(r"\s+", " ", ln).strip()
        if not ln:
            continue
        if any(re.search(p, ln, re.I) for p in NON_TITLE):
            continue
        if re.match(r"^\d+$", ln):
            continue
        if re.search(r"https?://", ln):
            continue
        lines.append(ln)
    return lines


def find_title(lines: list[str]) -> str:
    for ln in lines[:8]:
        if len(ln) < 4 or len(ln) > 120:
            continue
        if any(re.search(p, ln, re.I) for p in NON_TITLE):
            continue
        if re.search(r"\b(kcal|UH|P g|M g|GI|GO|Naziv namirnice)\b", ln, re.I):
            continue
        if re.search(r"\b(sastojci|priprema|način pripreme|nacin pripreme|postupak)\b", ln, re.I):
            continue
        if not re.search(r"[A-Za-zČĆŠĐŽčćšđž]", ln):
            continue
        return ln.strip(' -—•')
    return ""


def page_is_probably_recipe(lines: list[str]) -> bool:
    if len(lines) < 4:
        return False
    joined = "\n".join(lines)
    has_heading = any(re.search(p, joined, re.I) for p in ING_HEADINGS + STEP_HEADINGS)
    qty_lines = sum(bool(QTY_RE.match(ln)) or ln.startswith(('-', '•', '–')) for ln in lines)
    return has_heading or qty_lines >= 3


def compact_ingredient_lines(lines: list[str]) -> list[str]:
    out = []
    for ln in lines:
        if looks_like_nutri_or_sidebar(ln):
            continue
        if out and not QTY_RE.match(ln) and not ln.startswith(('-', '•', '–')) and len(ln) < 90 and not re.search(r"[\.!?]$", ln):
            prev = out[-1]
            if prev.endswith(',') or prev.endswith('(') or '(' in prev or len(prev) < 40:
                out[-1] = (prev + ' ' + ln).strip()
                continue
        out.append(ln)
    return out


def parse_ingredients(lines: list[str]) -> tuple[list[dict], int]:
    start = -1
    for i, ln in enumerate(lines):
        if any(re.search(p, ln, re.I) for p in ING_HEADINGS):
            start = i + 1
            break
    if start < 0:
        return [], -1
    end = len(lines)
    for i in range(start, len(lines)):
        if any(re.search(p, lines[i], re.I) for p in STEP_HEADINGS):
            end = i
            break
    block = compact_ingredient_lines(lines[start:end])
    out = []
    for ln in block:
        line = ln.lstrip('-•– ').strip()
        if not line or looks_like_nutri_or_sidebar(line):
            continue
        m = QTY_RE.match(line)
        if m:
            qty, item = normalize_ingredient_line(m.group(2), m.group(1))
        else:
            item, qty = normalize_ingredient_line(line, "")
        if item and not looks_like_nutri_or_sidebar(item):
            out.append({"item": item, "kolicina": qty})
    return out, end


def parse_steps(lines: list[str], from_idx: int) -> tuple[list[str], list[str]]:
    notes = []
    start = from_idx
    if start < 0:
        for i, ln in enumerate(lines):
            if any(re.search(p, ln, re.I) for p in STEP_HEADINGS):
                start = i + 1
                break
    if start < 0:
        return [], notes
    body_lines = []
    for ln in lines[start:]:
        if looks_like_nutri_or_sidebar(ln):
            notes.append(ln)
            continue
        body_lines.append(ln)
    body = " ".join(body_lines)
    steps = []
    for s in split_steps(body):
        if looks_like_nutri_or_sidebar(s):
            notes.append(s)
            continue
        s = re.sub(r"^\d+\s*[\)\.\-]\s*", "", s).strip()
        if len(s) >= 8:
            steps.append(s)
    return steps, notes


def extract_meta(lines: list[str]) -> tuple[int, int]:
    joined = " \n ".join(lines)
    porcije = 0
    vreme = 0
    m = re.search(r"\b(\d{1,2})\s*(?:porcije|porcija|osobe|osoba)\b", joined, re.I)
    if m:
        porcije = int(m.group(1))
    m = re.search(r"\b(\d{1,3})\s*(?:min|minuta)\b", joined, re.I)
    if m:
        vreme = int(m.group(1))
    return porcije, vreme


def parse_recipe_page(text: str, pdf_name: str, page_no: int, default_categories: list[str], default_tags: list[str], layout: str = 'auto') -> tuple[dict | None, dict]:
    lines = normalize_lines(text)
    debug = {"page": page_no, "lines": len(lines)}
    if not page_is_probably_recipe(lines):
        debug["skip"] = "not_recipe_like"
        return None, debug
    title = find_title(lines)
    if not title:
        debug["skip"] = "missing_title"
        return None, debug
    sastojci, step_idx = parse_ingredients(lines)
    koraci, notes = parse_steps(lines, step_idx)
    porcije, vreme = extract_meta(lines)
    if layout == 'carobna':
        notes = [n for n in notes if len(n) < 220]
    if len(sastojci) < 2 or len(koraci) < 1:
        debug["skip"] = f"weak_recipe ingredients={len(sastojci)} steps={len(koraci)}"
        return None, debug
    recipe = {
        "id": f"pdf_{slugify(title)}_{page_no}",
        "naziv": title,
        "kategorija": list(default_categories),
        "tags": list(default_tags),
        "porcije": porcije,
        "vreme_min": vreme,
        "tezina": "srednje",
        "sastojci": sastojci,
        "koraci": koraci,
        "napomene": " ".join(notes[:3]).strip(),
        "izvor": {
            "naziv": f"{pdf_name} (PDF)",
            "napomena": f"Automatska ekstrakcija, strana {page_no}",
            "url": "",
        },
    }
    debug["ok"] = True
    debug["title"] = title
    debug["ingredients"] = len(sastojci)
    debug["steps"] = len(koraci)
    return recipe, debug


def main():
    ap = argparse.ArgumentParser(description="Extract many recipes from one cookbook PDF into an import-ready pack.")
    ap.add_argument("input_pdf")
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--title", default="cookbook_pack")
    ap.add_argument("--category", action='append', default=[])
    ap.add_argument("--tag", action='append', default=[])
    ap.add_argument("--page-from", type=int, default=1)
    ap.add_argument("--page-to", type=int, default=0)
    ap.add_argument("--max-pages", type=int, default=0)
    ap.add_argument("--layout", choices=['auto','carobna'], default='auto')
    args = ap.parse_args()

    pdf_path = Path(args.input_pdf).expanduser().resolve()
    if not pdf_path.exists():
        raise SystemExit(f"PDF not found: {pdf_path}")

    pages = extract_pdf_pages(pdf_path, page_from=args.page_from, page_to=(args.page_to or None), max_pages=args.max_pages)
    recipes = []
    debug_pages = []
    for page_no, text in pages:
        recipe, dbg = parse_recipe_page(text, pdf_path.name, page_no, args.category, args.tag, layout=args.layout)
        debug_pages.append(dbg)
        if recipe:
            recipes.append(recipe)

    # Dedup by ID/title while keeping best quality-ish candidate.
    by_title = {}
    for rec in recipes:
        key = slugify(rec['naziv'])
        score = len(rec.get('sastojci', [])) * 2 + len(rec.get('koraci', [])) * 3
        if key not in by_title or score > by_title[key][0]:
            by_title[key] = (score, rec)
    final = [x[1] for x in by_title.values()]
    final.sort(key=lambda r: r['naziv'].lower())

    report = {
        "input_pdf": str(pdf_path),
        "title": args.title,
        "layout": args.layout,
        "pages_total_processed": len(pages),
        "recipes_found": len(final),
        "page_debug": debug_pages[:1000],
        "note": "Text-PDF best effort extractor. For scanned/image PDFs use OCR-first workflow.",
    }
    write_pack(Path(args.out_dir), args.title, final, report)
    print(f"Cookbook pack ready: {len(final)} recipes -> {args.out_dir}")


if __name__ == '__main__':
    main()
