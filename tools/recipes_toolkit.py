#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import csv
import io
import json
import math
import re
import unicodedata
from collections import Counter
from pathlib import Path
from typing import Iterable, Any

APP_NAME = "Paprikas Hub"


def strip_diacritics(s: str) -> str:
    return "".join(ch for ch in unicodedata.normalize("NFD", str(s or "")) if unicodedata.category(ch) != "Mn")


def slugify(s: str, fallback: str = "recept") -> str:
    s = strip_diacritics(str(s or "")).lower()
    s = re.sub(r"[^a-z0-9]+", "_", s)
    s = re.sub(r"_+", "_", s).strip("_")
    return s or fallback


def norm_key(s: str) -> str:
    s = strip_diacritics(str(s or "")).lower()
    s = re.sub(r"[^a-z0-9]+", " ", s)
    return re.sub(r"\s+", " ", s).strip()


def _read_text(path: Path) -> str:
    b = path.read_bytes()
    if b.startswith(b'\xef\xbb\xbf'):
        b = b[3:]
    return b.decode('utf-8', errors='replace')


def _extract_jsonish_blocks(text: str) -> list[str]:
    text = text.replace("```json", "```").replace("```ndjson", "```")
    fenced = re.findall(r"```\s*(.*?)```", text, flags=re.S)
    if fenced:
        return [x.strip() for x in fenced if x.strip()]
    return [text]


def _load_csv_text(text: str) -> list[dict]:
    sample = text[:3000]
    delimiter = ';' if sample.count(';') >= sample.count(',') else ','
    reader = csv.DictReader(io.StringIO(text), delimiter=delimiter)
    out = []
    for row in reader:
        if not row:
            continue
        out.append(dict(row))
    return out


def _load_txt_blocks(text: str) -> list[dict]:
    out = []
    blocks = re.split(r"\n\s*=+\s*(?:RECIPE|RECEPT)\s*=+\s*\n", text, flags=re.I)
    for block in blocks:
        b = block.strip()
        if not b:
            continue
        obj = {"naziv":"", "kategorija":[], "tags":[], "sastojci":[], "koraci":[], "napomene":""}
        mode = None
        for raw in b.splitlines():
            line = raw.strip()
            if not line:
                continue
            lower = line.lower()
            if lower.startswith("naziv:"):
                obj["naziv"] = line.split(':',1)[1].strip(); continue
            if lower.startswith("kategorija:"):
                obj["kategorija"] = [x.strip() for x in line.split(':',1)[1].split(',') if x.strip()]; continue
            if lower.startswith("tagovi:") or lower.startswith("tags:"):
                obj["tags"] = [x.strip().lstrip('#') for x in line.split(':',1)[1].split(',') if x.strip()]; continue
            if lower.startswith("porcije:"):
                obj["porcije"] = line.split(':',1)[1].strip(); continue
            if lower.startswith("vreme"):
                obj["vreme_min"] = line.split(':',1)[1].strip(); continue
            if lower.startswith("težina:") or lower.startswith("tezina:"):
                obj["tezina"] = line.split(':',1)[1].strip(); continue
            if lower.startswith("napomene:"):
                obj["napomene"] = line.split(':',1)[1].strip(); mode=None; continue
            if lower.startswith("sastojci"):
                mode = 'ing'; continue
            if lower.startswith("koraci"):
                mode = 'steps'; continue
            if mode == 'ing':
                line = re.sub(r"^[-•]\s*", "", line)
                parts = re.split(r"\s+[—\-:]\s+|\s+—\s+", line, maxsplit=1)
                if len(parts) == 2:
                    obj["sastojci"].append({"item": parts[0].strip(), "kolicina": parts[1].strip()})
                else:
                    obj["sastojci"].append({"item": line, "kolicina": ""})
                continue
            if mode == 'steps':
                line = re.sub(r"^\d+\s*[\)\.\-]\s*", "", line)
                obj["koraci"].append(line)
        if obj["naziv"]:
            out.append(obj)
    return out


def load_any(path: Path) -> list[dict]:
    text = _read_text(path)
    for chunk in _extract_jsonish_blocks(text):
        try:
            obj = json.loads(chunk)
            if isinstance(obj, list):
                return obj
            if isinstance(obj, dict):
                for key in ("recipes", "data", "items"):
                    if isinstance(obj.get(key), list):
                        return obj[key]
                return [obj]
        except Exception:
            pass
    lower_name = path.name.lower()
    if lower_name.endswith('.csv'):
        return _load_csv_text(text)
    if lower_name.endswith('.txt'):
        return _load_txt_blocks(text)

    out = []
    lines = [ln.strip() for ln in text.splitlines()]
    # Try NDJSON-ish parsing, skipping chatter lines.
    for line in lines:
        if not line:
            continue
        if line.startswith('```') or line.startswith('**CONTINUE') or line == '__CONTINUE__' or line == 'CONTINUE':
            continue
        if not line.startswith('{'):
            continue
        try:
            out.append(json.loads(line))
        except Exception:
            continue
    if out:
        return out

    # Last resort: parse TXT recipe blocks
    return _load_txt_blocks(text)


def as_list(val: Any) -> list[str]:
    if isinstance(val, list):
        return [str(x).strip() for x in val if str(x).strip()]
    if isinstance(val, str):
        parts = re.split(r"[,;|\n]+", val)
        return [p.strip() for p in parts if p.strip()]
    return []


def _to_int(val: Any) -> int:
    if val is None:
        return 0
    s = str(val).strip()
    if not s:
        return 0
    m = re.search(r"\d+", s)
    return int(m.group(0)) if m else 0


_NOISE_PATTERNS = [
    r"^Naziv namirnice \(100 g\)",
    r"\bkcal\b.*\bUH\b.*\bGI\b.*\bGO\b",
    r"\bšećer u krvi\b",
    r"\bholesterol\b",
    r"\bvitamin[a-zčćšđž]*\b",
    r"\bmineral[a-zčćšđž]*\b",
    r"\bglikemijsk[a-zčćšđž]*\b",
    r"\bkalorijsk[a-zčćšđž]*\b",
    r"\bspadaju u\b",
    r"\bpoboljšava\b",
    r"\botklanja\b",
    r"\bkoristi se\b",
    r"\bmože se jesti i svež\b",
]


def looks_like_nutri_or_sidebar(text: str) -> bool:
    s = str(text or "").strip()
    if not s:
        return False
    if len(s) > 90 and sum(bool(re.search(p, s, re.I)) for p in _NOISE_PATTERNS) >= 1:
        return True
    if re.search(r"Naziv namirnice \(100 g\)", s, re.I):
        return True
    if re.search(r"\b\d+(?:[\.,]\d+)?\s+\d+(?:[\.,]\d+)?\s+\d+(?:[\.,]\d+)?\s+\d+(?:[\.,]\d+)?", s):
        # table-like rows with many numbers
        return True
    return False


def normalize_ingredient_line(item: str, qty: str = "") -> tuple[str, str]:
    item = re.sub(r"\s+", " ", str(item or "").replace('\xa0', ' ')).strip(' -—•')
    qty = re.sub(r"\s+", " ", str(qty or "").replace('\xa0', ' ')).strip(' -—•')
    if not item and qty:
        item, qty = qty, ""
    # split "200 g šećera" to qty+item
    if item and not qty:
        m = re.match(r"^((?:oko\s+)?\d+[\d\s\.,/xX-]*\s*(?:kg|g|gr|mg|ml|l|dl|cl|kašike|kašika|kasike|kasika|šolje|solje|šolja|solja|kom|komada|lista|lista|veze|veza|glavice|glavica|čen[a-zčćšđž]+|pakovanja|pakovanje|prstohvat[a-zčćšđž]*))\s+(.+)$", item, re.I)
        if m:
            qty = m.group(1).strip()
            item = m.group(2).strip(' ,;')
    # strip trailing nutrition spillover
    item = re.split(r"\bNaziv namirnice \(100 g\)\b", item, maxsplit=1, flags=re.I)[0].strip(' ,;')
    return item, qty


def split_steps(text: str) -> list[str]:
    body = re.sub(r"\s+", " ", str(text or "")).strip()
    if not body:
        return []
    parts = re.split(r"(?<=[\.!?])\s+", body)
    out, buff = [], ""
    for p in parts:
        p = p.strip()
        if not p:
            continue
        if len(p) < 45 and not re.search(r"\d", p):
            buff = (buff + " " + p).strip()
            continue
        if buff:
            p = (buff + " " + p).strip()
            buff = ""
        out.append(p)
    if buff:
        out.append(buff)
    return [re.sub(r"\s+", " ", x).strip() for x in out if x.strip()]


def infer_tags(title: str, categories: list[str], tags: list[str]) -> list[str]:
    t = set(slugify(x).replace('_', '') for x in tags if x)
    title_l = strip_diacritics(title).lower()
    mapping = {
        'paprikas': ['paprikas'],
        'corba': ['corba', 'čorba'],
        'supa': ['supa'],
        'kolac': ['kolac', 'kolač'],
        'torta': ['torta'],
        'salata': ['salata'],
        'dorucak': ['dorucak', 'doručak'],
        'desert': ['desert', 'slatko', 'poslastica'],
        'peceno': ['pecen', 'pečeno', 'pecena', 'pečena'],
    }
    for tag, needles in mapping.items():
        if any(n in title_l for n in needles):
            t.add(tag)
    for c in categories:
        ck = slugify(c)
        if ck:
            t.add(ck)
    out = sorted({x for x in t if x})
    return out[:20]


def normalize_recipe(raw: dict, default_source_name: str = "web", default_source_note: str = "") -> tuple[dict | None, list[str]]:
    issues = []
    if not isinstance(raw, dict):
        return None, ["not-an-object"]
    naziv = str(raw.get("naziv") or raw.get("title") or raw.get("name") or "").strip()
    if not naziv:
        return None, ["missing-title"]
    naziv = re.sub(r"\s+", " ", naziv)
    rid = str(raw.get("id") or "").strip() or slugify(naziv)
    kategorija = [x.lower() for x in as_list(raw.get("kategorija") or raw.get("category"))]
    tags = [re.sub(r"^#", "", x.lower()) for x in as_list(raw.get("tags"))]
    porcije = _to_int(raw.get("porcije") or raw.get("servings"))
    vreme_min = _to_int(raw.get("vreme_min") or raw.get("time_min") or raw.get("vreme"))
    tezina = str(raw.get("tezina") or raw.get("difficulty") or "").strip().lower()
    if tezina not in {"lako", "srednje", "teško", "tesko"}:
        tezina = "srednje" if (raw.get("sastojci") or raw.get("koraci")) else ""
    if tezina == "tesko":
        tezina = "teško"

    sastojci_raw = raw.get("sastojci")
    sastojci = []
    if isinstance(sastojci_raw, list):
        for it in sastojci_raw:
            if isinstance(it, dict):
                item, qty = normalize_ingredient_line(it.get("item",""), it.get("kolicina",""))
            else:
                item, qty = normalize_ingredient_line(str(it), "")
            if not item:
                continue
            if looks_like_nutri_or_sidebar(item):
                issues.append("ingredient-noise")
                continue
            sastojci.append({"item": item, "kolicina": qty})
    elif isinstance(sastojci_raw, str):
        for line in re.split(r"\n+|\|", sastojci_raw):
            line = line.strip()
            if not line:
                continue
            if '—' in line:
                a,b = line.split('—',1)
            elif ':' in line:
                a,b = line.split(':',1)
            else:
                a,b = line, ''
            item, qty = normalize_ingredient_line(a,b)
            if item and not looks_like_nutri_or_sidebar(item):
                sastojci.append({"item": item, "kolicina": qty})

    koraci_raw = raw.get("koraci") or raw.get("steps")
    koraci = []
    if isinstance(koraci_raw, list):
        for s in koraci_raw:
            st = re.sub(r"\s+", " ", str(s or "")).strip()
            if not st:
                continue
            if looks_like_nutri_or_sidebar(st):
                issues.append("step-noise")
                continue
            koraci.append(st)
    elif isinstance(koraci_raw, str):
        for st in split_steps(koraci_raw):
            if not looks_like_nutri_or_sidebar(st):
                koraci.append(st)
            else:
                issues.append("step-noise")

    napomene = str(raw.get("napomene") or raw.get("notes") or "").strip()
    izvor = raw.get("izvor") if isinstance(raw.get("izvor"), dict) else {}
    src_name = str(izvor.get("naziv") or raw.get("source") or default_source_name).strip() or default_source_name
    src_note = str(izvor.get("napomena") or default_source_note).strip()
    src_url = str(izvor.get("url") or raw.get("url") or "").strip()

    tags = infer_tags(naziv, kategorija, tags)

    rec = {
        "id": rid,
        "naziv": naziv,
        "kategorija": kategorija,
        "tags": tags,
        "porcije": porcije,
        "vreme_min": vreme_min,
        "tezina": tezina or "srednje",
        "sastojci": sastojci,
        "koraci": koraci,
        "napomene": napomene,
        "izvor": {"naziv": src_name, "napomena": src_note, "url": src_url},
    }
    if not rec["sastojci"]:
        issues.append("missing-ingredients")
    if not rec["koraci"]:
        issues.append("missing-steps")
    return rec, issues


def quality_score(r: dict) -> int:
    return len(r.get("sastojci", [])) * 3 + len(r.get("koraci", [])) * 4 + (2 if r.get("porcije") else 0) + (2 if r.get("vreme_min") else 0)


def dedup_recipes(recipes: Iterable[dict], fuzzy: bool = True) -> tuple[list[dict], dict]:
    kept: dict[str, dict] = {}
    duplicates = []
    total = 0
    for raw in recipes:
        total += 1
        rec, _issues = normalize_recipe(raw) if not raw.get("id") or not raw.get("izvor") else (raw, [])
        if rec is None:
            continue
        key = norm_key(rec.get("naziv", ""))
        if not key:
            continue
        if key not in kept or quality_score(rec) > quality_score(kept[key]):
            if key in kept:
                duplicates.append({"type":"exact-title", "kept": kept[key].get("id"), "dropped": rec.get("id"), "key": key})
            kept[key] = rec
        else:
            duplicates.append({"type":"exact-title", "kept": kept[key].get("id"), "dropped": rec.get("id"), "key": key})
    if fuzzy:
        keys = sorted(list(kept.keys()))
        removed = set()
        for i, k1 in enumerate(keys):
            if k1 in removed or k1 not in kept:
                continue
            t1 = set(k1.split())
            r1 = kept[k1]
            ing1 = {norm_key(x.get('item','')) for x in r1.get('sastojci', []) if x.get('item')}
            for k2 in keys[i+1:]:
                if k2 in removed or k2 not in kept:
                    continue
                t2 = set(k2.split())
                if not t1 or not t2:
                    continue
                jacc = len(t1 & t2) / max(1, len(t1 | t2))
                if jacc < 0.72:
                    continue
                r2 = kept[k2]
                ing2 = {norm_key(x.get('item','')) for x in r2.get('sastojci', []) if x.get('item')}
                ing_j = len(ing1 & ing2) / max(1, len(ing1 | ing2)) if ing1 and ing2 else 0.0
                if ing_j >= 0.55 or (jacc >= 0.86 and abs(len(ing1)-len(ing2)) <= 2):
                    best_key = k1 if quality_score(r1) >= quality_score(r2) else k2
                    drop_key = k2 if best_key == k1 else k1
                    duplicates.append({"type":"fuzzy", "kept": kept[best_key].get("id"), "dropped": kept[drop_key].get("id"), "keys":[best_key, drop_key], "title_jaccard": round(jacc, 3), "ingredient_jaccard": round(ing_j, 3)})
                    removed.add(drop_key)
        for rk in removed:
            kept.pop(rk, None)
    final = sorted(kept.values(), key=lambda r: norm_key(r.get("naziv", "")))
    report = {"total_in": total, "total_out": len(final), "duplicates": duplicates[:500]}
    return final, report


def to_wrapped_payload(recipes: list[dict]) -> dict:
    return {"app": APP_NAME, "kind": "recipes-bulk", "version": "v1", "recipes": recipes}


def csv_rows(recipes: list[dict]) -> str:
    out = io.StringIO()
    writer = csv.writer(out, delimiter=';')
    writer.writerow(["id","naziv","kategorija","tags","porcije","vreme_min","tezina","sastojci","koraci","napomene","izvor_naziv","izvor_napomena","izvor_url"])
    for r in recipes:
        writer.writerow([
            r.get("id",""),
            r.get("naziv",""),
            ",".join(r.get("kategorija",[])),
            ",".join(r.get("tags",[])),
            r.get("porcije",0),
            r.get("vreme_min",0),
            r.get("tezina",""),
            "|".join(f"{x.get('item','')}—{x.get('kolicina','')}" for x in r.get("sastojci",[])),
            "|".join(r.get("koraci",[])),
            r.get("napomene",""),
            r.get("izvor",{}).get("naziv",""),
            r.get("izvor",{}).get("napomena",""),
            r.get("izvor",{}).get("url",""),
        ])
    return out.getvalue()


def txt_blocks(recipes: list[dict]) -> str:
    parts = []
    for r in recipes:
        parts.append("==== RECIPE ====")
        parts.append(f"Naziv: {r.get('naziv','')}")
        parts.append(f"Kategorija: {', '.join(r.get('kategorija',[]))}")
        parts.append(f"Tagovi: {', '.join(r.get('tags',[]))}")
        parts.append(f"Porcije: {r.get('porcije',0)}")
        parts.append(f"Vreme(min): {r.get('vreme_min',0)}")
        parts.append(f"Težina: {r.get('tezina','')}")
        parts.append("")
        parts.append("Sastojci:")
        for x in r.get("sastojci", []):
            parts.append(f"- {x.get('item','')} — {x.get('kolicina','')}")
        parts.append("")
        parts.append("Koraci:")
        for i, s in enumerate(r.get("koraci", []), 1):
            parts.append(f"{i}) {s}")
        if r.get("napomene"):
            parts.append("")
            parts.append(f"Napomene: {r.get('napomene','')}")
        parts.append("")
    return "\n".join(parts)


def html_book(recipes: list[dict], title: str) -> str:
    def esc(s: Any) -> str:
        return str(s).replace('&','&amp;').replace('<','&lt;').replace('>','&gt;')
    items = []
    for r in recipes:
        ing_html = ''.join(
            '<li><b>{}</b> - {}</li>'.format(esc(x.get('item','')), esc(x.get('kolicina','')))
            for x in r.get('sastojci',[])
        )
        step_html = ''.join('<li>{}</li>'.format(esc(x)) for x in r.get('koraci',[]))
        meta = '{} - {}'.format(esc(', '.join(r.get('kategorija',[]))), esc(', '.join('#'+t for t in r.get('tags',[]))))
        items.append("<section class='card'><h2>{}</h2><div class='meta'>{}</div><h3>Sastojci</h3><ul>{}</ul><h3>Koraci</h3><ol>{}</ol></section>".format(
            esc(r.get('naziv','')), meta, ing_html, step_html
        ))
    return "<!doctype html><html lang='sr'><head><meta charset='utf-8'><meta name='viewport' content='width=device-width, initial-scale=1'><title>{}</title><style>body{{font-family:system-ui,sans-serif;background:#f7f9fc;margin:0;padding:16px}}.wrap{{max-width:980px;margin:0 auto}}.card{{background:#fff;border:1px solid #dde5ee;border-radius:16px;padding:14px;margin:12px 0}}h1{{margin:0 0 10px}}h2{{margin:0 0 6px}}.meta{{color:#556070;font-size:13px}}ul,ol{{margin-top:6px}}@media print{{body{{background:#fff;padding:0}}.card{{break-inside:avoid}}}}</style></head><body><div class='wrap'><h1>{}</h1><div class='meta'>Ukupno recepata: {}</div>{}</div></body></html>".format(esc(title), esc(title), len(recipes), ''.join(items))

def write_pack(out_dir: Path, title: str, recipes: list[dict], report: dict | None = None) -> dict:
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / 'recipes_wrapped.json').write_text(json.dumps(to_wrapped_payload(recipes), ensure_ascii=False, indent=2) + "\n", encoding='utf-8')
    (out_dir / 'recipes.json').write_text(json.dumps(recipes, ensure_ascii=False, indent=2) + "\n", encoding='utf-8')
    with (out_dir / 'recipes.ndjson').open('w', encoding='utf-8') as f:
        for r in recipes:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    (out_dir / 'recipes.csv').write_text(csv_rows(recipes), encoding='utf-8')
    (out_dir / 'recipes.txt').write_text(txt_blocks(recipes), encoding='utf-8')
    (out_dir / 'recipes.html').write_text(html_book(recipes, title), encoding='utf-8')
    rep = report or {}
    rep.setdefault('count', len(recipes))
    (out_dir / 'report.json').write_text(json.dumps(rep, ensure_ascii=False, indent=2) + "\n", encoding='utf-8')
    return rep
