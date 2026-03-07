#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Paprikas Hub local server (static files + JSON DB API).

- Serves index.html and all static files from project root
- Persists browser state immediately into data/db/app_state.json
- Uses append-only events log + atomic file writes
"""
from __future__ import annotations

import argparse
import io
import json
import os
import re
import shutil
import sys
from datetime import datetime, timezone
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from pathlib import Path
from threading import Lock
from urllib.parse import urlparse, parse_qs
import urllib.request

try:
    import pdfplumber  # optional (PDF import tools)
except Exception:  # pragma: no cover
    pdfplumber = None

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data" / "db"
DB_FILE = DATA_DIR / "app_state.json"
EVENTS_FILE = DATA_DIR / "events.ndjson"
BACKUP_DIR = DATA_DIR / "backups"
WRITE_LOCK = Lock()
ALLOWED_KEY_PREFIX = "paprikasHub"
PH_RECIPE_LS_KEY = "paprikasHubRecipesUserV1"



def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace('+00:00', 'Z')


def ensure_paths() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    if not DB_FILE.exists():
        payload = {
            "meta": {
                "app": "Paprikas Hub",
                "version": "v5.1",
                "db_format": "json-state-v1",
                "created_utc": utc_now(),
                "updated_utc": utc_now(),
            },
            "data": {},
        }
        atomic_write_json(DB_FILE, payload)
    EVENTS_FILE.touch(exist_ok=True)


def atomic_write_json(path: Path, payload: dict) -> None:
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    os.replace(tmp, path)


def load_db() -> dict:
    ensure_paths()
    try:
        return json.loads(DB_FILE.read_text(encoding="utf-8"))
    except Exception:
        bad = DB_FILE.with_name(DB_FILE.stem + '.corrupt-' + datetime.now().strftime('%Y%m%d-%H%M%S') + DB_FILE.suffix)
        shutil.copy2(DB_FILE, bad)
        payload = {
            "meta": {
                "app": "Paprikas Hub",
                "version": "v5.1",
                "db_format": "json-state-v1",
                "created_utc": utc_now(),
                "updated_utc": utc_now(),
                "recovered": True,
            },
            "data": {},
        }
        atomic_write_json(DB_FILE, payload)
        return payload


def append_event(event: dict) -> None:
    EVENTS_FILE.parent.mkdir(parents=True, exist_ok=True)
    with EVENTS_FILE.open('a', encoding='utf-8') as f:
        f.write(json.dumps(event, ensure_ascii=False) + "\n")


def save_db(payload: dict, make_backup: bool = False) -> None:
    payload.setdefault('meta', {})
    payload['meta']['updated_utc'] = utc_now()
    if make_backup:
        stamp = datetime.now().strftime('%Y%m%d-%H%M%S')
        backup = BACKUP_DIR / f"app_state-{stamp}.json"
        if DB_FILE.exists():
            shutil.copy2(DB_FILE, backup)
    atomic_write_json(DB_FILE, payload)



def slugify(s: str) -> str:
    s = s.strip().lower()
    s = re.sub(r"[\s\-]+", "_", s)
    s = re.sub(r"[^a-z0-9_šđčćžáéíóúàèìòùâêîôûäëïöüñ]+", "", s)
    # map common Serbian diacritics to latin basic
    rep = {
        "š":"s","đ":"dj","č":"c","ć":"c","ž":"z",
        "á":"a","é":"e","í":"i","ó":"o","ú":"u",
        "à":"a","è":"e","ì":"i","ò":"o","ù":"u",
        "â":"a","ê":"e","î":"i","ô":"o","û":"u",
        "ä":"a","ë":"e","ï":"i","ö":"o","ü":"u",
        "ñ":"n",
    }
    for k,v in rep.items():
        s = s.replace(k,v)
    s = re.sub(r"_+", "_", s).strip("_")
    return s or "recept"



def _pdf_norm_lines(raw: str) -> list[str]:
    lines: list[str] = []
    for ln in raw.splitlines():
        l = ln.replace("\xa0", " ").strip()
        l = re.sub(r"\s+", " ", l)
        if not l:
            continue
        if re.search(r"https?://", l):
            continue
        if re.match(r"^(Page|Strana)\s+\d+", l, re.I):
            continue
        if re.match(r"^\d+$", l):
            continue
        lines.append(l)
    return lines


def _pdf_title(lines: list[str]) -> str:
    for l in lines[:8]:
        if len(l) < 4 or len(l) > 120:
            continue
        if re.search(r"\b(sastojci|priprema|način pripreme|nacin pripreme|postupak)\b", l, re.I):
            continue
        if re.search(r"\b(kcal|UH|P g|M g|GI|GO|Naziv namirnice)\b", l, re.I):
            continue
        if not re.search(r"[A-Za-zČĆŠĐŽčćšđž]", l):
            continue
        return l.strip(" -—•")
    return lines[0].strip(" -—•") if lines else ""


def _pdf_is_noise(s: str) -> bool:
    if not s:
        return False
    if re.search(r"Naziv namirnice \(100 g\)", s, re.I):
        return True
    if re.search(r"\bkcal\b.*\bUH\b.*\bGI\b.*\bGO\b", s, re.I):
        return True
    if len(s) > 80 and re.search(r"\b(holesterol|vitamin|minerali|šećer u krvi|glikemijsk|kalorijsk|poboljšava|otklanja)\b", s, re.I):
        return True
    return False


def _pdf_norm_ing(item: str, qty: str = "") -> tuple[str, str]:
    item = re.sub(r"\s+", " ", str(item or "")).strip(" -—•")
    qty = re.sub(r"\s+", " ", str(qty or "")).strip(" -—•")
    if item and not qty:
        m = re.match(r"^((?:oko\s+)?\d+[\d\s\.,/xX-]*\s*(?:kg|g|gr|mg|ml|l|dl|cl|kašike|kašika|kasike|kasika|šolje|solje|šolja|solja|kom|komada|lista|veze|veza|glavice|glavica|čena|čen[a-zčćšđž]+|pakovanja|pakovanje|prstohvat[a-zčćšđž]*))\s+(.+)$", item, re.I)
        if m:
            qty = m.group(1).strip()
            item = m.group(2).strip()
    item = re.split(r"\bNaziv namirnice \(100 g\)\b", item, maxsplit=1, flags=re.I)[0].strip(" ,;")
    return item, qty


def _pdf_split_steps(text: str) -> list[str]:
    text = re.sub(r"\s+", " ", text).strip()
    if not text:
        return []
    parts = re.split(r"(?<=[\.!?])\s+", text)
    out: list[str] = []
    buff = ""
    for p in parts:
        p = p.strip()
        if not p:
            continue
        if len(p) < 40 and not re.search(r"\d", p):
            buff = (buff + " " + p).strip()
            continue
        if buff:
            p = (buff + " " + p).strip()
            buff = ""
        out.append(p)
    if buff:
        out.append(buff)
    return [x for x in out if x]


def recipe_from_pdf_bytes(pdf_bytes: bytes) -> tuple[dict, list[str]]:
    warnings: list[str] = []
    try:
        if pdfplumber is None:
            raise RuntimeError('pdfplumber nije instaliran. Instaliraj: pip install pdfplumber')
        with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
            pages = []
            for p in pdf.pages[:10]:
                pages.append(p.extract_text() or "")
        raw = "\n".join(pages)
    except Exception as e:
        raise ValueError(f"PDF parse error: {e}")

    lines = _pdf_norm_lines(raw)
    if not lines:
        raise ValueError("PDF nema čitljiv tekst (pokušaj drugi PDF ili scan/OCR).")

    title = _pdf_title(lines)
    porcije = 0
    vreme_min = 0
    joined = " \n ".join(lines)
    m = re.search(r"\b(\d{1,2})\s*(?:porcije|porcija|osobe|osoba)\b", joined, re.I)
    if m:
        porcije = int(m.group(1))
    m = re.search(r"\b(\d{1,3})\s*(?:min|minuta)\b", joined, re.I)
    if m:
        vreme_min = int(m.group(1))

    ing_start = -1
    for i, l in enumerate(lines):
        if re.search(r"\bsastojci\b|\bpotrebno je\b", l, re.I):
            ing_start = i + 1
            break
    step_start = -1
    for i, l in enumerate(lines):
        if re.search(r"\b(priprema|način pripreme|nacin pripreme|postupak|kako se priprema)\b", l, re.I):
            step_start = i + 1
            break

    sastojci: list[dict] = []
    if ing_start >= 0:
        ing_end = step_start - 1 if step_start > ing_start else len(lines)
        block = []
        for l in lines[ing_start:ing_end]:
            if _pdf_is_noise(l):
                continue
            if block and not re.match(r"^[-•–]", l) and not re.match(r"^(?:oko\s+)?\d", l, re.I) and len(l) < 90 and not re.search(r"[\.!?]$", l):
                prev = block[-1]
                if prev.endswith(',') or prev.endswith('(') or '(' in prev or len(prev) < 40:
                    block[-1] = (prev + ' ' + l).strip()
                    continue
            block.append(l)
        for l in block:
            item_line = l.lstrip('-•– ').strip()
            if not item_line:
                continue
            qm = re.match(r"^((?:oko\s+)?\d+[\d\s\.,/xX-]*\s*(?:kg|g|gr|mg|ml|l|dl|cl|kašike|kašika|kasike|kasika|šolje|solje|šolja|solja|kom|komada|lista|veze|veza|glavice|glavica|čena|čen[a-zčćšđž]+|pakovanja|pakovanje|prstohvat[a-zčćšđž]*))\s+(.+)$", item_line, re.I)
            if qm:
                qty, item = _pdf_norm_ing(qm.group(2), qm.group(1))
            else:
                item, qty = _pdf_norm_ing(item_line, "")
            if item and not _pdf_is_noise(item):
                sastojci.append({"item": item, "kolicina": qty})
    else:
        warnings.append("Nisam našao jasan heading za sastojke.")

    koraci: list[str] = []
    napomene = []
    if step_start >= 0:
        body_lines = []
        for l in lines[step_start:]:
            if _pdf_is_noise(l):
                napomene.append(l)
                continue
            body_lines.append(l)
        for st in _pdf_split_steps(" ".join(body_lines)):
            st = re.sub(r"^\d+\s*[\)\.\-]\s*", "", st).strip()
            if not st:
                continue
            if _pdf_is_noise(st):
                napomene.append(st)
                continue
            koraci.append(st)
    else:
        warnings.append("Nisam našao jasan heading za pripremu.")

    if len(sastojci) < 1:
        warnings.append("Lista sastojaka je slaba ili prazna - proveri PDF format / layout.")
    if len(koraci) < 1:
        warnings.append("Koraci pripreme nisu jasno prepoznati - proveri PDF format / layout.")

    # Derive rough categories/tags from title
    title_l = title.lower()
    kategorija = []
    if "čorba" in title_l or "corba" in title_l:
        kategorija.append("čorbe")
    elif "supa" in title_l:
        kategorija.append("supe")
    elif any(x in title_l for x in ["torta", "kolač", "kolac", "baklava", "pita"]):
        kategorija.append("poslastice")
    tags = []
    for tag in ["paprikas", "corba", "supa", "salata", "kolac", "desert", "dorucak"]:
        if tag in re.sub(r"[^a-zčćšđž]+", " ", title_l):
            tags.append(tag)

    recipe = {
        "id": slugify(title),
        "naziv": title,
        "kategorija": kategorija,
        "tags": tags,
        "porcije": porcije,
        "vreme_min": vreme_min,
        "tezina": "srednje",
        "sastojci": sastojci,
        "koraci": koraci,
        "napomene": " ".join(napomene[:3]).strip(),
        "izvor": {"naziv": "PDF import", "url": "", "napomena": "Automatski import iz PDF-a"},
    }
    return recipe, warnings

def api_response(handler: 'PaprikasHandler', code: int, body: dict) -> None:
    raw = json.dumps(body, ensure_ascii=False).encode('utf-8')
    handler.send_response(code)
    handler.send_header('Content-Type', 'application/json; charset=utf-8')
    handler.send_header('Content-Length', str(len(raw)))
    handler.send_header('Cache-Control', 'no-store')
    handler.send_cors_headers()
    handler.end_headers()
    handler.wfile.write(raw)


def parse_multipart_form_bytes(content_type: str, body: bytes) -> dict[str, dict]:
    from email.parser import BytesParser
    from email.policy import default

    if 'multipart/form-data' not in (content_type or '').lower():
        raise ValueError('Expected multipart/form-data')
    raw = (f"Content-Type: {content_type}\r\nMIME-Version: 1.0\r\n\r\n".encode('utf-8') + body)
    msg = BytesParser(policy=default).parsebytes(raw)
    out: dict[str, dict] = {}
    for part in msg.iter_parts():
        if part.get_content_disposition() != 'form-data':
            continue
        name = part.get_param('name', header='content-disposition')
        if not name:
            continue
        out[str(name)] = {
            'filename': part.get_filename(),
            'content_type': part.get_content_type(),
            'data': part.get_payload(decode=True) or b'',
        }
    return out


def fetch_remote_json(url: str) -> dict | list:
    if not re.match(r'^https?://', url or '', re.I):
        raise ValueError('Dozvoljeni su samo http/https URL-ovi')
    req = urllib.request.Request(url, headers={'User-Agent': 'PaprikasHub/5.13'})
    with urllib.request.urlopen(req, timeout=20) as resp:  # nosec B310 - controlled http/https only
        ctype = resp.headers.get('Content-Type', '')
        raw = resp.read()
    if 'json' not in ctype.lower() and not url.lower().endswith('.json'):
        raise ValueError('Remote odgovor nije JSON')
    try:
        return json.loads(raw.decode('utf-8'))
    except Exception as e:
        raise ValueError(f'Remote JSON parse error: {e}')


# =========================
# Pipeline (Content Studio)
# =========================
PIPELINE_DIR = PROJECT_ROOT / "data" / "pipeline"
PIPE_BATCHES = PIPELINE_DIR / "batches"
PIPE_TITLES = PIPELINE_DIR / "titles"
PIPE_OUT = PIPELINE_DIR / "out"
PIPE_STATE = PIPELINE_DIR / "pipeline_state.json"
PIPE_SESSION_LOG = PIPELINE_DIR / "session_log.json"
ATLAS_IMPORT_HISTORY = PIPELINE_DIR / "atlas_import_history.json"


# health cache (in-memory)
PIPE_HEALTH_CACHE = {}  # batch -> {"mtime": float, "soft_kolicina": bool, "data": dict}


def ensure_pipeline_paths() -> None:
    PIPE_BATCHES.mkdir(parents=True, exist_ok=True)
    PIPE_TITLES.mkdir(parents=True, exist_ok=True)
    PIPE_OUT.mkdir(parents=True, exist_ok=True)
    if not PIPE_STATE.exists():
        PIPE_STATE.write_text(json.dumps({"created_utc": utc_now(), "done": {}}, ensure_ascii=False, indent=2), encoding="utf-8")
    if not PIPE_SESSION_LOG.exists():
        PIPE_SESSION_LOG.write_text(json.dumps({"created_utc": utc_now(), "items": []}, ensure_ascii=False, indent=2), encoding="utf-8")
    if not ATLAS_IMPORT_HISTORY.exists():
        ATLAS_IMPORT_HISTORY.write_text(json.dumps({"created_utc": utc_now(), "items": []}, ensure_ascii=False, indent=2), encoding="utf-8")

def _count_nonempty_lines(path: Path) -> int:
    if not path.exists():
        return 0
    n = 0
    with path.open("r", encoding="utf-8", errors="ignore") as f:
        for ln in f:
            if ln.strip():
                n += 1
    return n

def _load_inventory_titles() -> set[str]:
    # prefer latest exported prompt-ready file in data/exports
    exports_dir = PROJECT_ROOT / "data" / "exports"
    candidates = sorted(exports_dir.glob("recipe_inventory_titles_prompt_ready*.txt"))
    if not candidates:
        return set()
    p = candidates[-1]
    titles = set()
    with p.open("r", encoding="utf-8", errors="ignore") as f:
        for ln in f:
            s = ln.strip().lstrip("-").strip()
            if s:
                titles.add(_normalize_title(s))
    return titles

def _normalize_title(s: str) -> str:
    s = s.strip().lower()
    s = re.sub(r"\s+", " ", s)
    s = s.strip(" .,-;:!?/\\|")
    for pref in ("recept za ", "recept: ", "recept ", "kako napraviti ", "kako se pravi "):
        if s.startswith(pref):
            s = s[len(pref):].strip()
            break
    return s

def _send_bytes(handler: "PaprikasHandler", raw: bytes, filename: str, ctype: str = "application/octet-stream") -> None:
    handler.send_response(200)
    handler.send_header("Content-Type", ctype)
    handler.send_header("Content-Length", str(len(raw)))
    handler.send_header("Content-Disposition", f'attachment; filename="{filename}"')
    handler.send_header("Cache-Control", "no-store")
    handler.send_cors_headers()
    handler.end_headers()
    handler.wfile.write(raw)


def _session_log_read_raw() -> dict:
    ensure_pipeline_paths()
    try:
        return json.loads(PIPE_SESSION_LOG.read_text(encoding="utf-8"))
    except Exception:
        return {"created_utc": utc_now(), "items": []}

def _session_log_write_raw(data: dict) -> None:
    ensure_pipeline_paths()
    PIPE_SESSION_LOG.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

def _time_local_string() -> str:
    try:
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    except Exception:
        return utc_now()

def pipeline_log_add(action: str, batch: str | None = None, note: str = "", lines: int | None = None) -> dict:
    data = _session_log_read_raw()
    items = data.get("items") if isinstance(data.get("items"), list) else []
    entry = {
        "session_log_items": len(_session_log_read_raw().get("items", [])),
        "time_utc": utc_now(),
        "time_local": _time_local_string(),
        "action": action,
        "batch": batch or "",
        "lines": lines if isinstance(lines, int) else None,
        "note": note or "",
    }
    items.insert(0, entry)
    data["items"] = items[:300]
    _session_log_write_raw(data)
    return entry

def pipeline_log_read() -> dict:
    data = _session_log_read_raw()
    items = data.get("items") if isinstance(data.get("items"), list) else []
    return {"ok": True, "items": items[:100]}



def _batch_health_compute(batch: str, soft_kolicina: bool = True) -> dict:
    ensure_pipeline_paths()
    fp = PIPE_BATCHES / f"batch-{batch}.ndjson"
    if not fp.exists():
        return {"ok": True, "batch": batch, "health": "EMPTY", "issues": ["missing_file"], "metrics": {"lines": 0}, "soft_kolicina": soft_kolicina}
    mtime = fp.stat().st_mtime
    cache = PIPE_HEALTH_CACHE.get(batch)
    if cache and cache.get("mtime") == mtime and cache.get("soft_kolicina") == soft_kolicina:
        return cache["data"]

    required = ["naziv","kategorija","tags","porcije","vreme_min","tezina","sastojci","koraci","napomene"]
    total = 0
    parse_err = 0
    not_obj = 0
    missing_req = 0
    empty_kol = 0
    steps_min = None
    steps_sum = 0
    ingr_min = None
    ingr_sum = 0
    titles_norm = set()
    dup_in_batch = 0

    def _norm_title(s: str) -> str:
        s = s.strip().lower()
        s = re.sub(r"\s+", " ", s)
        s = s.strip(" .,-;:!?/\\|")
        for pref in ("recept za ", "recept: ", "recept ", "kako napraviti ", "kako se pravi "):
            if s.startswith(pref):
                s = s[len(pref):].strip()
                break
        return s

    valid_objs = 0
    with fp.open("r", encoding="utf-8", errors="ignore") as f:
        for ln in f:
            ln = ln.strip()
            if not ln:
                continue
            total += 1
            try:
                obj = json.loads(ln)
            except Exception:
                parse_err += 1
                continue
            if not isinstance(obj, dict):
                not_obj += 1
                continue
            # required keys
            if any(k not in obj for k in required):
                missing_req += 1
                continue

            valid_objs += 1

            kor = obj.get("koraci")
            klen = len([x for x in kor if isinstance(x, str) and x.strip()]) if isinstance(kor, list) else 0
            ing = obj.get("sastojci")
            if isinstance(ing, list):
                ilen = len([x for x in ing if isinstance(x, dict) and str(x.get("item","")).strip()])
                empty_kol += len([x for x in ing if isinstance(x, dict) and not str(x.get("kolicina","")).strip()])
            else:
                ilen = 0

            steps_sum += klen
            ingr_sum += ilen
            steps_min = klen if steps_min is None else min(steps_min, klen)
            ingr_min = ilen if ingr_min is None else min(ingr_min, ilen)

            tn = _norm_title(str(obj.get("naziv") or ""))
            if tn:
                if tn in titles_norm:
                    dup_in_batch += 1
                else:
                    titles_norm.add(tn)

    denom = max(1, valid_objs)
    metrics = {
        "lines": total,
        "parse_err": parse_err,
        "not_object": not_obj,
        "missing_required": missing_req,
        "dup_in_batch": dup_in_batch,
        "empty_kolicina": empty_kol,
        "avg_steps": round(steps_sum / denom, 2),
        "min_steps": int(steps_min or 0),
        "avg_ingredients": round(ingr_sum / denom, 2),
        "min_ingredients": int(ingr_min or 0),
        "valid_objects": valid_objs,
    }

    issues = []
    if total == 0:
        health = "EMPTY"
        issues.append("empty_batch")
    else:
        if parse_err: issues.append(f"invalid_json:{parse_err}")
        if not_obj: issues.append(f"not_object:{not_obj}")
        if missing_req: issues.append(f"missing_fields:{missing_req}")
        if dup_in_batch: issues.append(f"dup_titles_in_batch:{dup_in_batch}")
        if metrics["min_steps"] < 2: issues.append("too_few_steps:min<2")
        if metrics["min_ingredients"] < 3: issues.append("too_few_ingredients:min<3")
        if empty_kol: issues.append(f"empty_kolicina:{empty_kol}")

        severe = (parse_err >= 5) or (missing_req >= 5) or (metrics["min_steps"] == 0) or (metrics["min_ingredients"] == 0)
        moderate = (parse_err > 0) or (missing_req > 0) or (metrics["min_steps"] < 2) or (metrics["min_ingredients"] < 3) or (dup_in_batch > 0)

        health = "BAD" if severe else ("WARN" if moderate else "OK")

    data = {"ok": True, "batch": batch, "health": health, "issues": issues, "metrics": metrics, "soft_kolicina": soft_kolicina}
    PIPE_HEALTH_CACHE[batch] = {"mtime": mtime, "soft_kolicina": soft_kolicina,
        "use_cleaned": use_cleaned, "data": data}
    return data


def pipeline_quality_gate(soft_kolicina: bool = True) -> dict:
    """
    Quality gate: BLOCK if any batch has health == BAD.
    Uses health summary.
    """
    summary = pipeline_health_summary(soft_kolicina=soft_kolicina).get("items", {})
    counts = {"OK": 0, "WARN": 0, "BAD": 0, "EMPTY": 0}
    bad_batches = []
    for b, info in summary.items():
        h = str((info or {}).get("health") or "EMPTY")
        if h not in counts:
            counts[h] = 0
        counts[h] += 1
        if h == "BAD":
            bad_batches.append({
                "batch": b,
                "health": h,
                "issues": (info or {}).get("issues", []),
                "metrics": (info or {}).get("metrics", {}),
            })
    gate = {
        "ok": True,
        "pass": (counts.get("BAD", 0) == 0),
        "bad_count": int(counts.get("BAD", 0)),
        "counts": counts,
        "bad_batches": bad_batches,
        "soft_kolicina": soft_kolicina,
    }
    return gate

def pipeline_health_summary(soft_kolicina: bool = True) -> dict:
    ensure_pipeline_paths()
    out = {}
    for i in range(1, 11):
        b = f"{i:03d}"
        out[b] = _batch_health_compute(b, soft_kolicina=soft_kolicina)
    return {"ok": True, "items": out, "soft_kolicina": soft_kolicina}

def pipeline_batch_detail(batch: str) -> dict:
    ensure_pipeline_paths()
    if not re.fullmatch(r"\d{3}", batch):
        raise ValueError("Invalid batch")
    fp = PIPE_BATCHES / f"batch-{batch}.ndjson"
    tp = PIPE_TITLES / f"batch-{batch}-titles.txt"
    lines = _count_nonempty_lines(fp) if fp.exists() else 0
    titles_count = _count_nonempty_lines(tp) if tp.exists() else 0
    cleaned_fp = PIPE_BATCHES / f"batch-{batch}.cleaned.ndjson"
    invalid_fp = PIPE_BATCHES / f"batch-{batch}.invalid.ndjson"
    cleaned_lines = _count_nonempty_lines(cleaned_fp) if cleaned_fp.exists() else 0
    invalid_lines = _count_nonempty_lines(invalid_fp) if invalid_fp.exists() else 0
    has_cleaned = cleaned_fp.exists() and cleaned_lines > 0
    has_invalid = invalid_fp.exists() and invalid_lines > 0
    status_label = "nije krenuto"
    health_data = _batch_health_compute(batch, soft_kolicina=True)
    if lines >= 100:
        status_label = "spremno"
    elif lines > 0:
        status_label = "u toku"
    log_raw = _session_log_read_raw()
    items = log_raw.get("items") if isinstance(log_raw.get("items"), list) else []
    batch_items = [it for it in items if str(it.get("batch") or "") == batch][:20]
    note_items = [it for it in batch_items if str(it.get("note") or "").strip()]
    last_note = str(note_items[0].get("note") or "") if note_items else ""
    return {
        "ok": True,
        "batch": batch,
        "lines": lines,
        "missing_to_100": max(0, 100 - int(lines)),
        "titles_count": titles_count,
        "has_cleaned": has_cleaned,
        "cleaned_lines": cleaned_lines,
        "has_invalid": has_invalid,
        "invalid_lines": invalid_lines,
        "cleaned_file": cleaned_fp.name,
        "invalid_file": invalid_fp.name,
        "note_count": len(note_items),
        "last_note": last_note,
        "status_label": status_label,
        "log_items": batch_items[:8],
        "health": health_data.get("health"),
        "health_issues": health_data.get("issues", []),
        "health_metrics": health_data.get("metrics", {}),
    }

def pipeline_status_payload() -> dict:
    ensure_pipeline_paths()
    inv = _load_inventory_titles()
    batches_total = 0
    done: dict = {}
    files: dict = {}
    for i in range(1, 11):
        b = f"{i:03d}"
        p = PIPE_BATCHES / f"batch-{b}.ndjson"
        c = _count_nonempty_lines(p)
        files[b] = {"exists": p.exists(), "lines": c}
        if c > 0:
            batches_total += c
            done[f"u{b}"] = True
    # titles
    for i in range(1, 11):
        b = f"{i:03d}"
        t = PIPE_TITLES / f"batch-{b}-titles.txt"
        if t.exists() and _count_nonempty_lines(t) > 0:
            done[f"t{b}"] = True
    all_prev = PIPE_TITLES / "all-previous-titles.txt"
    if all_prev.exists() and _count_nonempty_lines(all_prev) > 0:
        done["mt"] = True
    merged = PIPE_OUT / "recipes_1000_merged.ndjson"
    report = PIPE_OUT / "recipes_1000_merged_report.json"
    merged_written = 0
    if report.exists():
        try:
            j = json.loads(report.read_text(encoding="utf-8"))
            merged_written = int(j.get("written_merged") or 0)
        except Exception:
            merged_written = _count_nonempty_lines(merged)
    if merged.exists() and _count_nonempty_lines(merged) > 0:
        done["merge"] = True
        done["dl"] = True

    # base_total: try read manifest count quickly (not expensive: already loaded in app anyway) -> compute as "unknown" here
    payload = {
        "ok": True,
        "inventory_titles": len(inv),
        "batches_total_lines": batches_total,
        "merged_written": merged_written,
        "base_total": None,
        "files": files,
        "done": done,
        "session_log_items": len(_session_log_read_raw().get("items", [])),
        "time_utc": utc_now(),
    }
    return payload

def pipeline_save_batch(batch: str, text: str) -> None:
    ensure_pipeline_paths()
    if not re.fullmatch(r"\d{3}", batch):
        raise ValueError("Invalid batch")
    p = PIPE_BATCHES / f"batch-{batch}.ndjson"
    p.write_text(text.strip() + "\n", encoding="utf-8")

def pipeline_extract_titles(batch: str) -> int:
    ensure_pipeline_paths()
    if not re.fullmatch(r"\d{3}", batch):
        raise ValueError("Invalid batch")
    src = PIPE_BATCHES / f"batch-{batch}.ndjson"
    if not src.exists():
        raise ValueError("Batch file not found")
    titles: list[str] = []
    with src.open("r", encoding="utf-8", errors="ignore") as f:
        for ln in f:
            ln = ln.strip()
            if not ln:
                continue
            try:
                obj = json.loads(ln)
                if isinstance(obj, dict):
                    t = str(obj.get("naziv") or "").strip()
                    if t:
                        titles.append(t)
            except Exception:
                continue
    out = PIPE_TITLES / f"batch-{batch}-titles.txt"
    out.write_text("\n".join(titles) + ("\n" if titles else ""), encoding="utf-8")
    return len(titles)

def pipeline_merge_titles() -> int:
    ensure_pipeline_paths()
    inv = _load_inventory_titles()
    all_titles: list[str] = []
    # keep as raw for user prompts, but dedupe by normalized
    seen = set(inv)
    # include inventory in output too (as "- title" lines)
    for tnorm in sorted(inv):
        all_titles.append(tnorm)
    for i in range(1, 11):
        b = f"{i:03d}"
        p = PIPE_TITLES / f"batch-{b}-titles.txt"
        if not p.exists():
            continue
        with p.open("r", encoding="utf-8", errors="ignore") as f:
            for ln in f:
                t = ln.strip()
                if not t:
                    continue
                n = _normalize_title(t)
                if n in seen:
                    continue
                seen.add(n)
                all_titles.append(n)
    out = PIPE_TITLES / "all-previous-titles.txt"
    out.write_text("\n".join(all_titles) + ("\n" if all_titles else ""), encoding="utf-8")
    return len(all_titles)

# Merge engine (autofix + sanitizer + validate + dedupe)
# =========================
# Recipe Atlas auto-import (server-side)
# =========================
def _recipe_norm_title(s: str) -> str:
    s = str(s or "").strip().lower()
    s = re.sub(r"\s+", " ", s)
    s = s.strip(" .,-;:!?/\\|")
    for pref in ("recept za ", "recept: ", "recept ", "kako napraviti ", "kako se pravi "):
        if s.startswith(pref):
            s = s[len(pref):].strip()
            break
    return s

def _recipe_slugify(s: str) -> str:
    # approximate client phSlugify (ASCII-ish)
    s = str(s or "").lower().strip()
    s = re.sub(r"\s+", " ", s)
    # remove diacritics roughly by mapping common serbian chars
    table = str.maketrans({
        "č":"c","ć":"c","đ":"dj","š":"s","ž":"z",
        "Č":"c","Ć":"c","Đ":"dj","Š":"s","Ž":"z"
    })
    s = s.translate(table)
    s = re.sub(r"[^a-z0-9]+", "_", s)
    s = re.sub(r"^_+|_+$", "", s)
    return s or "recept"

def _recipe_quality(r: dict) -> int:
    try:
        return int(len(r.get("sastojci") or []))*3 + int(len(r.get("koraci") or []))*4 + (2 if r.get("porcije") else 0) + (2 if r.get("vreme_min") else 0) + (1 if r.get("user") else 0)
    except Exception:
        return 0

def _recipe_parse_normalized(o: dict) -> dict | None:
    try:
        naziv = str(o.get("naziv") or "").strip()
        if not naziv:
            return None
        rid = str(o.get("id") or "").strip() or _recipe_slugify(naziv)

        tags = o.get("tags")
        if isinstance(tags, list):
            tags = [str(x).strip() for x in tags if str(x).strip()]
        else:
            tags = [s.strip() for s in str(tags or "").split(",") if s.strip()]

        kat = o.get("kategorija")
        if isinstance(kat, list):
            kat = [str(x).strip() for x in kat if str(x).strip()]
        else:
            kat = [s.strip() for s in str(kat or "").split(",") if s.strip()]

        por = o.get("porcije")
        try:
            por = int(por)
        except Exception:
            por = 0
        tim = o.get("vreme_min")
        try:
            tim = int(tim)
        except Exception:
            tim = 0

        tez = str(o.get("tezina") or "lako").strip().lower() or "lako"
        if tez not in {"lako","srednje","teško"}:
            if "lak" in tez: tez="lako"
            elif "sred" in tez: tez="srednje"
            elif "tes" in tez or "teš" in tez: tez="teško"
            else: tez="lako"

        nap = str(o.get("napomene") or "").strip()

        sast = []
        if isinstance(o.get("sastojci"), list):
            for x in o["sastojci"]:
                if isinstance(x, dict):
                    item = str(x.get("item") or "").strip()
                    kol = str(x.get("kolicina") or "").strip()
                    if item:
                        sast.append({"item": item, "kolicina": kol})
        elif isinstance(o.get("sastojci"), str):
            for line in re.split(r"\n+", o["sastojci"]):
                line = line.strip()
                if not line:
                    continue
                parts = re.split(r"—|-|:", line, maxsplit=1)
                item = (parts[0] or "").strip()
                kol = (parts[1] or "").strip() if len(parts) > 1 else ""
                if item:
                    sast.append({"item": item, "kolicina": kol})

        kor = []
        if isinstance(o.get("koraci"), list):
            kor = [str(x).strip() for x in o["koraci"] if str(x).strip()]
        elif isinstance(o.get("koraci"), str):
            kor = [s.strip() for s in re.split(r"\n+", o["koraci"]) if s.strip()]
        elif isinstance(o.get("steps"), str):
            kor = [s.strip() for s in re.split(r"\n+", o["steps"]) if s.strip()]
        elif isinstance(o.get("steps"), list):
            kor = [str(x).strip() for x in o["steps"] if str(x).strip()]

        izvor = o.get("izvor")
        if not isinstance(izvor, dict):
            izvor = {"naziv":"", "napomena":""}

        return {
            "id": rid,
            "naziv": naziv,
            "kategorija": kat,
            "tags": tags,
            "porcije": por,
            "vreme_min": tim,
            "tezina": tez,
            "sastojci": sast,
            "koraci": kor,
            "napomene": nap,
            "izvor": izvor,
            "user": True,
            "updated_utc": utc_now(),
        }
    except Exception:
        return None

def _recipes_merge_unique(base_arr: list, incoming_arr: list) -> tuple[list, int]:
    by_key = {}
    replaced = 0
    def put(r):
        nonlocal replaced
        if not r or not r.get("id"):
            return
        keys = [str(r.get("id")), "t:" + _recipe_norm_title(r.get("naziv",""))]
        existing = None
        for k in keys:
            if k in by_key:
                existing = by_key[k]
                break
        chosen = r
        if existing:
            chosen = r if _recipe_quality(r) >= _recipe_quality(existing) else existing
            if chosen is r and existing is not r:
                replaced += 1
        for k in keys:
            by_key[k] = chosen
    for r in base_arr or []:
        put(r)
    for r in incoming_arr or []:
        put(r)
    uniq = {}
    for r in by_key.values():
        if r and r.get("id"):
            uniq[str(r["id"])] = r
    return list(uniq.values()), replaced


def _atlas_hist_read_raw() -> dict:
    ensure_pipeline_paths()
    try:
        return json.loads(ATLAS_IMPORT_HISTORY.read_text(encoding="utf-8"))
    except Exception:
        return {"created_utc": utc_now(), "items": []}

def _atlas_hist_write_raw(data: dict) -> None:
    ensure_pipeline_paths()
    ATLAS_IMPORT_HISTORY.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

def atlas_hist_add(entry: dict) -> None:
    data = _atlas_hist_read_raw()
    items = data.get("items") if isinstance(data.get("items"), list) else []
    items.insert(0, entry)
    data["items"] = items[:50]
    _atlas_hist_write_raw(data)

def atlas_hist_list(limit: int = 20) -> dict:
    data = _atlas_hist_read_raw()
    items = data.get("items") if isinstance(data.get("items"), list) else []
    return {"ok": True, "items": items[:max(0, min(int(limit), 50))]}

def atlas_make_backup(tag: str = "atlas-import") -> str:
    ensure_paths()
    stamp = datetime.now().strftime('%Y%m%d-%H%M%S')
    name = f"app_state-{tag}-{stamp}.json"
    dst = BACKUP_DIR / name
    if DB_FILE.exists():
        shutil.copy2(DB_FILE, dst)
    return name

def atlas_rollback_last() -> dict:
    ensure_pipeline_paths()
    hist = _atlas_hist_read_raw()
    items = hist.get("items") if isinstance(hist.get("items"), list) else []
    if not items:
        raise ValueError("No import history found")
    last = items[0]
    backup_name = str(last.get("backup") or "").strip()
    if not backup_name:
        raise ValueError("No backup recorded for last import")
    backup_path = BACKUP_DIR / backup_name
    if not backup_path.exists():
        raise ValueError("Backup file not found: " + backup_name)

    with WRITE_LOCK:
        # restore DB
        shutil.copy2(backup_path, DB_FILE)
        db = load_db()
        db.setdefault("data", {})
        data = db["data"]
        value = data.get(PH_RECIPE_LS_KEY, "[]")
        append_event({"ts": utc_now(), "op":"atlas_rollback_last", "backup": backup_name, "key": PH_RECIPE_LS_KEY})
        save_db(db)
    pipeline_log_add("atlas_rollback_last", batch="", note=f"Rollback applied. backup={backup_name}")
    return {"ok": True, "backup": backup_name, "key": PH_RECIPE_LS_KEY, "value": value}

def pipeline_atlas_auto_import(rel_file: str = "out/recipes_1000_merged.ndjson", make_backup: bool = True) -> dict:
    # read merged NDJSON from pipeline dir and import into paprikasHubRecipesUserV1 in server DB
    ensure_pipeline_paths()
    if not rel_file:
        raise ValueError("Missing file")
    safe = (PIPELINE_DIR / rel_file).resolve()
    if not str(safe).startswith(str(PIPELINE_DIR.resolve())):
        raise ValueError("Not allowed")
    if not safe.exists() or not safe.is_file():
        raise ValueError("Merged file not found")

    # load incoming recipes
    incoming = []
    invalid = 0
    with safe.open("r", encoding="utf-8", errors="ignore") as f:
        for ln in f:
            ln = ln.strip()
            if not ln:
                continue
            try:
                obj = json.loads(ln)
            except Exception:
                invalid += 1
                continue
            if not isinstance(obj, dict):
                invalid += 1
                continue
            rec = _recipe_parse_normalized(obj)
            if rec:
                incoming.append(rec)
            else:
                invalid += 1

    # load existing from DB key
    with WRITE_LOCK:
        db = load_db()
        db.setdefault("data", {})
        data = db["data"]
        raw = data.get(PH_RECIPE_LS_KEY, "")
        base = []
        if raw:
            try:
                parsed = json.loads(raw)
                if isinstance(parsed, list):
                    base = [x for x in parsed if isinstance(x, dict)]
            except Exception:
                base = []
        merged, replaced = _recipes_merge_unique(base, incoming)

        # backup DB before write
        backup_name = ""
        if make_backup:
            backup_name = atlas_make_backup(tag='atlas-import')

        data[PH_RECIPE_LS_KEY] = json.dumps(merged, ensure_ascii=False)
        append_event({"ts": utc_now(), "op": "atlas_auto_import", "key": PH_RECIPE_LS_KEY, "incoming": len(incoming), "invalid": invalid, "merged": len(merged), "replaced": replaced})
        save_db(db)

    pipeline_log_add("atlas_auto_import", batch="", lines=len(incoming), note=f"Auto-import merged->Atlas: incoming={len(incoming)}, invalid={invalid}, merged_total={len(merged)}, replaced={replaced}")

    
    # record import history
    atlas_hist_add({
        "time_utc": utc_now(),
        "file": rel_file,
        "backup": backup_name,
        "incoming": len(incoming),
        "invalid": invalid,
        "before": len(base),
        "after": len(merged),
        "replaced": replaced,
    })
    return {
        "ok": True,
        "file": rel_file,
        "incoming": len(incoming),
        "invalid": invalid,
        "before": len(base),
        "after": len(merged),
        "replaced": replaced,
        "key": PH_RECIPE_LS_KEY,
        "value": data.get(PH_RECIPE_LS_KEY, ""),
    }


TEZINA_ALLOWED = {"lako","srednje","teško"}

def _clean_str(x) -> str:
    if x is None:
        return ""
    if not isinstance(x, str):
        x = str(x)
    return re.sub(r"\s+", " ", x).strip()

def _to_int(x):
    if isinstance(x, int):
        return x
    if isinstance(x, float) and x.is_integer():
        return int(x)
    if isinstance(x, str):
        s = x.strip()
        if s.isdigit():
            return int(s)
        m = re.search(r"(\d+)", s)
        if m:
            return int(m.group(1))
    return None

def _split_list_str(s: str) -> list[str]:
    parts = re.split(r"[;,|]+", s)
    out = []
    for p in parts:
        p = _clean_str(p)
        if p:
            out.append(p)
    return out

def _split_koraci(s: str) -> list[str]:
    s = s.replace("\r\n", "\n")
    lines = [ln.strip() for ln in s.split("\n") if ln.strip()]
    if len(lines) <= 1:
        parts = re.split(r"\s*\|\s*|\s*;\s*", s)
        parts = [p.strip() for p in parts if p.strip()]
        return parts if parts else ([s.strip()] if s.strip() else [])
    cleaned = []
    for ln in lines:
        ln2 = re.sub(r"^\s*\d+\s*[\)\.\-:]\s*", "", ln).strip()
        cleaned.append(ln2 if ln2 else ln)
    return cleaned

def _parse_sastojak_line(line: str) -> dict | None:
    line = _clean_str(line)
    if not line:
        return None
    m = re.split(r"\s*[-:]\s*", line, maxsplit=1)
    if len(m) == 2:
        item = _clean_str(m[0])
        kol = _clean_str(m[1])
        if item or kol:
            return {"item": item, "kolicina": kol}
    if re.match(r"^\d", line):
        parts = line.split(" ", 1)
        if len(parts) == 2:
            return {"item": _clean_str(parts[1]), "kolicina": _clean_str(parts[0])}
    return {"item": line, "kolicina": ""}

def _normalize_list_str(lst) -> list[str]:
    if not isinstance(lst, list):
        return []
    out = []
    seen = set()
    for it in lst:
        s = _clean_str(it)
        if not s:
            continue
        key = s.lower()
        if key in seen:
            continue
        seen.add(key)
        out.append(s)
    return out

def _normalize_tezina(x) -> str:
    s = _clean_str(x).lower()
    mapping = {"laka":"lako","lak":"lako","easy":"lako","srednja":"srednje","medium":"srednje","teska":"teško","tesko":"teško","hard":"teško"}
    s = mapping.get(s, s)
    if s in TEZINA_ALLOWED:
        return s
    if "lak" in s: return "lako"
    if "sred" in s: return "srednje"
    if "teš" in s or "tes" in s: return "teško"
    return s

def _autofix(obj: dict) -> tuple[dict, list[str]]:
    notes = []
    out = dict(obj)
    if "napomene" not in out or out.get("napomene") is None:
        out["napomene"] = ""
        notes.append("autofix:napomene_added")
    if "naziv" in out:
        out["naziv"] = _clean_str(out.get("naziv"))
    if isinstance(out.get("napomene"), str):
        out["napomene"] = _clean_str(out.get("napomene"))
    for key in ("tags","kategorija"):
        val = out.get(key)
        if isinstance(val, str):
            out[key] = _split_list_str(val)
            notes.append(f"autofix:{key}_str_to_list")
        elif isinstance(val, list):
            out[key] = [_clean_str(x) for x in val if _clean_str(x)]
    for key in ("porcije","vreme_min"):
        if key in out:
            v = _to_int(out.get(key))
            if v is not None:
                if out.get(key) != v:
                    notes.append(f"autofix:{key}_to_int")
                out[key] = v
    if "tezina" in out:
        out["tezina"] = _clean_str(out.get("tezina")).lower()
    kor = out.get("koraci")
    if isinstance(kor, str):
        out["koraci"] = _split_koraci(kor)
        notes.append("autofix:koraci_str_to_list")
    elif isinstance(kor, list):
        out["koraci"] = [_clean_str(x) for x in kor if _clean_str(x)]
    sast = out.get("sastojci")
    if isinstance(sast, str):
        lines = re.split(r"\n|;", sast)
        parsed = []
        for ln in lines:
            rec = _parse_sastojak_line(ln)
            if rec: parsed.append(rec)
        out["sastojci"] = parsed
        notes.append("autofix:sastojci_str_to_listobj")
    elif isinstance(sast, list):
        if all(isinstance(x, str) for x in sast):
            parsed = []
            for ln in sast:
                rec = _parse_sastojak_line(ln)
                if rec: parsed.append(rec)
            out["sastojci"] = parsed
            notes.append("autofix:sastojci_liststr_to_listobj")
        elif all(isinstance(x, dict) for x in sast):
            cleaned = []
            for it in sast:
                item = _clean_str(it.get("item"))
                kol = _clean_str(it.get("kolicina"))
                if item or kol:
                    cleaned.append({"item": item, "kolicina": kol})
            out["sastojci"] = cleaned
    return out, notes

def _sanitize(obj: dict) -> tuple[dict, list[str]]:
    notes = []
    out = dict(obj)
    out["naziv"] = _clean_str(out.get("naziv"))
    out["napomene"] = _clean_str(out.get("napomene",""))
    out["kategorija"] = _normalize_list_str(out.get("kategorija"))
    out["tags"] = _normalize_list_str(out.get("tags"))
    p = _to_int(out.get("porcije"))
    if p is not None:
        out["porcije"] = p
    else:
        notes.append("porcije:not_int")
    vm = _to_int(out.get("vreme_min"))
    if vm is not None:
        out["vreme_min"] = vm
    else:
        notes.append("vreme_min:not_int")
    out["tezina"] = _normalize_tezina(out.get("tezina"))
    koraci = out.get("koraci")
    if isinstance(koraci, list):
        cleaned = []
        for k in koraci:
            s = _clean_str(k)
            if s: cleaned.append(s)
        out["koraci"] = cleaned
    sast = out.get("sastojci")
    if isinstance(sast, list):
        cleaned = []
        for it in sast:
            if not isinstance(it, dict):
                continue
            item = _clean_str(it.get("item"))
            kol = _clean_str(it.get("kolicina"))
            if not item and not kol:
                continue
            cleaned.append({"item": item, "kolicina": kol})
        out["sastojci"] = cleaned
    return out, notes

def _validate(obj: dict, strict: bool, soft_kolicina: bool) -> tuple[bool, list[str]]:
    errs = []
    required = ["naziv","kategorija","tags","porcije","vreme_min","tezina","sastojci","koraci","napomene"]
    for k in required:
        if k not in obj:
            errs.append(f"missing:{k}")
    if errs:
        return False, errs
    if not isinstance(obj.get("naziv"), str) or not obj["naziv"].strip():
        errs.append("naziv:empty")
    if not isinstance(obj.get("kategorija"), list) or not all(isinstance(x,str) and x.strip() for x in obj["kategorija"]):
        errs.append("kategorija:bad")
    if not isinstance(obj.get("tags"), list) or not all(isinstance(x,str) and x.strip() for x in obj["tags"]):
        errs.append("tags:bad")
    if not isinstance(obj.get("porcije"), int) or obj["porcije"] <= 0:
        errs.append("porcije:bad")
    if not isinstance(obj.get("vreme_min"), int) or obj["vreme_min"] <= 0:
        errs.append("vreme_min:bad")
    tez = obj.get("tezina")
    if not isinstance(tez, str) or tez not in TEZINA_ALLOWED:
        errs.append("tezina:bad")
    if not isinstance(obj.get("sastojci"), list):
        errs.append("sastojci:bad")
    else:
        for i,it in enumerate(obj["sastojci"]):
            if not isinstance(it, dict):
                errs.append(f"sastojci[{i}]:bad")
                continue
            if not isinstance(it.get("item"), str) or not it["item"].strip():
                errs.append(f"sastojci[{i}].item:empty")
            if not soft_kolicina:
                if not isinstance(it.get("kolicina"), str) or not it["kolicina"].strip():
                    errs.append(f"sastojci[{i}].kolicina:empty")
    if not isinstance(obj.get("koraci"), list) or not all(isinstance(x,str) and x.strip() for x in obj["koraci"]):
        errs.append("koraci:bad")
    if not isinstance(obj.get("napomene"), str):
        errs.append("napomene:bad")
    if strict:
        if isinstance(obj.get("koraci"), list) and len(obj["koraci"]) < 2:
            errs.append("strict:koraci_too_short")
        if isinstance(obj.get("sastojci"), list) and len(obj["sastojci"]) < 4:
            errs.append("strict:sastojci_too_few")
    return (len(errs)==0), errs

def pipeline_run_merge(autofix: bool, strict: bool, soft_kolicina: bool, use_cleaned: bool = False) -> dict:
    ensure_pipeline_paths()
    inv = _load_inventory_titles()
    seen = set(inv)
    merged_path = PIPE_OUT / "recipes_1000_merged.ndjson"
    invalid_path = PIPE_OUT / "recipes_1000_invalid_lines.ndjson"
    dup_path = PIPE_OUT / "recipes_1000_duplicates.ndjson"
    report_path = PIPE_OUT / "recipes_1000_merged_report.json"
    auto_notes_path = PIPE_OUT / "recipes_1000_autofix_notes.json"
    san_notes_path = PIPE_OUT / "recipes_1000_sanitizer_notes.json"

    stats = {
        "session_log_items": len(_session_log_read_raw().get("items", [])),
        "time_utc": utc_now(),
        "strict": strict,
        "autofix": autofix,
        "soft_kolicina": soft_kolicina,
        "inventory_titles_loaded": len(inv),
        "total_lines_read": 0,
        "valid_lines": 0,
        "invalid_lines": 0,
        "duplicate_lines": 0,
        "written_merged": 0,
        "files": [],
    }
    auto_counter = {}
    san_counter = {}

    def _bfiles():
        for i in range(1, 11):
            b = f"{i:03d}"
            raw = PIPE_BATCHES / f"batch-{b}.ndjson"
            cleaned = PIPE_BATCHES / f"batch-{b}.cleaned.ndjson"
            fp = cleaned if (use_cleaned and cleaned.exists() and _count_nonempty_lines(cleaned) > 0) else raw
            yield b, fp

    with merged_path.open("w", encoding="utf-8") as f_m, \
         invalid_path.open("w", encoding="utf-8") as f_i, \
         dup_path.open("w", encoding="utf-8") as f_d:
        for b, fp in _bfiles():
            file_stat = {"batch": b, "exists": fp.exists(), "lines": 0, "valid": 0, "invalid": 0, "dup": 0, "written": 0}
            if not fp.exists():
                stats["files"].append(file_stat)
                continue
            with fp.open("r", encoding="utf-8", errors="ignore") as f:
                for ln in f:
                    ln = ln.strip()
                    if not ln:
                        continue
                    stats["total_lines_read"] += 1
                    file_stat["lines"] += 1
                    try:
                        obj = json.loads(ln)
                    except Exception:
                        stats["invalid_lines"] += 1
                        file_stat["invalid"] += 1
                        f_i.write(ln + "\n")
                        continue
                    if not isinstance(obj, dict):
                        stats["invalid_lines"] += 1
                        file_stat["invalid"] += 1
                        f_i.write(json.dumps(obj, ensure_ascii=False) + "\n")
                        continue

                    if autofix:
                        obj, notes = _autofix(obj)
                        for n in notes:
                            auto_counter[n] = auto_counter.get(n, 0) + 1
                    obj, notes2 = _sanitize(obj)
                    for n in notes2:
                        san_counter[n] = san_counter.get(n, 0) + 1

                    ok, errs = _validate(obj, strict=strict, soft_kolicina=soft_kolicina)
                    if not ok:
                        stats["invalid_lines"] += 1
                        file_stat["invalid"] += 1
                        f_i.write(json.dumps(obj, ensure_ascii=False) + "\n")
                        continue
                    stats["valid_lines"] += 1
                    file_stat["valid"] += 1

                    tn = _normalize_title(obj.get("naziv",""))
                    if tn in seen:
                        stats["duplicate_lines"] += 1
                        file_stat["dup"] += 1
                        f_d.write(json.dumps(obj, ensure_ascii=False) + "\n")
                        continue
                    seen.add(tn)
                    f_m.write(json.dumps(obj, ensure_ascii=False) + "\n")
                    stats["written_merged"] += 1
                    file_stat["written"] += 1

            stats["files"].append(file_stat)

    report_path.write_text(json.dumps(stats, ensure_ascii=False, indent=2), encoding="utf-8")
    auto_notes_path.write_text(json.dumps(auto_counter, ensure_ascii=False, indent=2), encoding="utf-8")
    san_notes_path.write_text(json.dumps(san_counter, ensure_ascii=False, indent=2), encoding="utf-8")

    # bundle reports zip
    import zipfile as _zip
    bundle = PIPE_OUT / "reports_bundle.zip"
    with _zip.ZipFile(bundle, "w", compression=_zip.ZIP_DEFLATED) as z:
        for p in [report_path, auto_notes_path, san_notes_path, invalid_path, dup_path]:
            if p.exists():
                z.write(p, arcname=p.name)
    pipeline_log_add("run_merge", batch="", lines=int(stats.get("written_merged") or 0), note=f'Merge završen. invalid={int(stats.get("invalid_lines") or 0)}, dup={int(stats.get("duplicate_lines") or 0)}')
    return stats




def pipeline_quick_fix_all(soft_kolicina: bool = True) -> dict:
    ensure_pipeline_paths()
    results = []
    total_written = 0
    total_invalid = 0
    for i in range(1, 11):
        b = f"{i:03d}"
        fp = PIPE_BATCHES / f"batch-{b}.ndjson"
        if not fp.exists() or _count_nonempty_lines(fp) == 0:
            continue
        try:
            r = pipeline_quick_fix(batch=b, soft_kolicina=soft_kolicina)
            results.append(r)
            total_written += int(r.get("written_cleaned") or 0)
            total_invalid += int(r.get("invalid_lines") or 0)
        except Exception as e:
            results.append({"ok": False, "batch": b, "error": str(e)})
    pipeline_log_add("quick_fix_all", batch="", note=f"Quick fix all finished. cleaned_total={total_written}, invalid_total={total_invalid}")
    return {"ok": True, "results": results, "cleaned_total": total_written, "invalid_total": total_invalid}

def pipeline_promote_cleaned(batch: str, keep_backup: bool = True) -> dict:
    ensure_pipeline_paths()
    if not re.fullmatch(r"\d{3}", batch):
        raise ValueError("Invalid batch")
    raw = PIPE_BATCHES / f"batch-{batch}.ndjson"
    cleaned = PIPE_BATCHES / f"batch-{batch}.cleaned.ndjson"
    if not cleaned.exists() or _count_nonempty_lines(cleaned) == 0:
        raise ValueError("No cleaned batch found")
    backup_name = ""
    if keep_backup and raw.exists() and _count_nonempty_lines(raw) > 0:
        backup_name = f"batch-{batch}.bak-{datetime.now().strftime('%Y%m%d-%H%M%S')}.ndjson"
        shutil.copyfile(raw, PIPE_BATCHES / backup_name)
    shutil.copyfile(cleaned, raw)
    pipeline_log_add("promote_cleaned", batch=batch, note=f"Promoted cleaned -> raw. backup={backup_name}")
    return {"ok": True, "batch": batch, "backup": backup_name, "raw_file": raw.name, "cleaned_file": cleaned.name}

def pipeline_quick_fix(batch: str, soft_kolicina: bool = True) -> dict:
    """
    Read batch-XYZ.ndjson, apply _autofix + _sanitize, validate softly,
    and write:
      - batch-XYZ.cleaned.ndjson
      - batch-XYZ.invalid.ndjson
    """
    ensure_pipeline_paths()
    if not re.fullmatch(r"\d{3}", batch):
        raise ValueError("Invalid batch")
    src = PIPE_BATCHES / f"batch-{batch}.ndjson"
    if not src.exists():
        raise ValueError("Batch file not found")

    cleaned = PIPE_BATCHES / f"batch-{batch}.cleaned.ndjson"
    invalid = PIPE_BATCHES / f"batch-{batch}.invalid.ndjson"

    total = 0
    written = 0
    invalid_count = 0
    parse_err = 0
    autofix_notes = {}

    def _add_note(key: str):
        autofix_notes[key] = int(autofix_notes.get(key, 0)) + 1

    with src.open("r", encoding="utf-8", errors="ignore") as f_in, \
         cleaned.open("w", encoding="utf-8") as f_ok, \
         invalid.open("w", encoding="utf-8") as f_bad:
        for ln in f_in:
            raw = ln.strip()
            if not raw:
                continue
            total += 1
            try:
                obj = json.loads(raw)
            except Exception:
                parse_err += 1
                invalid_count += 1
                f_bad.write(raw + "\n")
                continue
            if not isinstance(obj, dict):
                invalid_count += 1
                f_bad.write(json.dumps(obj, ensure_ascii=False) + "\n")
                continue

            obj, anotes = _autofix(obj)
            for n in anotes:
                _add_note(n)
            obj, snotes = _sanitize(obj)
            for n in snotes:
                _add_note("sanitize:" + n)

            ok, errs = _validate(obj, strict=False, soft_kolicina=soft_kolicina)
            if ok:
                f_ok.write(json.dumps(obj, ensure_ascii=False) + "\n")
                written += 1
            else:
                invalid_count += 1
                f_bad.write(json.dumps(obj, ensure_ascii=False) + "\n")

    note = f"Quick fix završen za batch {batch}. cleaned={written}, invalid={invalid_count}, parse_err={parse_err}"
    pipeline_log_add("quick_fix", batch=batch, lines=written, note=note)

    return {
        "ok": True,
        "batch": batch,
        "source_file": src.name,
        "cleaned_file": cleaned.name,
        "invalid_file": invalid.name,
        "total_lines": total,
        "written_cleaned": written,
        "invalid_lines": invalid_count,
        "parse_err": parse_err,
        "autofix_notes": autofix_notes,
        "soft_kolicina": soft_kolicina,
    }

def pipeline_export_all_zip() -> Path:
    ensure_pipeline_paths()
    import zipfile as _zip
    out_zip = PIPE_OUT / f"pipeline_export_{datetime.now().strftime('%Y%m%d-%H%M%S')}.zip"
    with _zip.ZipFile(out_zip, "w", compression=_zip.ZIP_DEFLATED) as z:
        # batches, titles, out (excluding huge merged? include)
        for folder, prefix in [(PIPE_BATCHES,"batches"), (PIPE_TITLES,"titles"), (PIPE_OUT,"out")]:
            for p in folder.rglob("*"):
                if p.is_file():
                    z.write(p, arcname=f"{prefix}/{p.name}")
    pipeline_log_add("export_all", batch="", note=f"Napravljen backup zip: {out_zip.name}")
    return out_zip


class ReusableThreadingHTTPServer(ThreadingHTTPServer):
    allow_reuse_address = True


class PaprikasHandler(SimpleHTTPRequestHandler):
    server_version = "PaprikasHubServer/0.2"

    def __init__(self, *args, directory=None, **kwargs):
        super().__init__(*args, directory=str(PROJECT_ROOT), **kwargs)

    def log_message(self, fmt: str, *args) -> None:
        sys.stderr.write("[%s] %s\n" % (self.log_date_time_string(), fmt % args))

    def send_cors_headers(self) -> None:
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')

    def end_headers(self):
        self.send_header('X-Content-Type-Options', 'nosniff')
        super().end_headers()

    def do_OPTIONS(self):
        self.send_response(204)
        if self.path.startswith('/api/'):
            self.send_cors_headers()
        self.end_headers()

    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path
        if path == '/api/ping':
            return api_response(self, 200, {
                'ok': True,
                'service': 'paprikas-json-db',
                'time_utc': utc_now(),
                'db_file': str(DB_FILE.relative_to(PROJECT_ROOT)),
            })
        if path == '/api/db':
            with WRITE_LOCK:
                db = load_db()
            return api_response(self, 200, {
                'ok': True,
                'meta': db.get('meta', {}),
                'data': db.get('data', {}),
            })
        if path == '/api/db/export':
            with WRITE_LOCK:
                db = load_db()
            return api_response(self, 200, {'ok': True, 'db': db})
        if path == '/api/recipes/fetch_json':
            try:
                qs = parse_qs(parsed.query or '')
                url = (qs.get('url') or [''])[0]
                if not url:
                    return api_response(self, 400, {'ok': False, 'error': 'Missing url'})
                payload = fetch_remote_json(url)
                return api_response(self, 200, payload if isinstance(payload, dict) else {'recipes': payload})
            except Exception as e:
                return api_response(self, 400, {'ok': False, 'error': str(e)})

        
        if path == '/api/pipeline/status':
            try:
                return api_response(self, 200, pipeline_status_payload())
            except Exception as e:
                return api_response(self, 400, {'ok': False, 'error': str(e)})

        if path == '/api/pipeline/atlas_import_history':
            try:
                qs = parse_qs(parsed.query or '')
                limit = int((qs.get('limit') or ['20'])[0])
                return api_response(self, 200, atlas_hist_list(limit=limit))
            except Exception as e:
                return api_response(self, 400, {'ok': False, 'error': str(e)})

        if path == '/api/pipeline/quality_gate':
            try:
                qs = parse_qs(parsed.query or '')
                soft = (qs.get('soft_kolicina') or ['1'])[0]
                soft_kolicina = (soft != '0')
                return api_response(self, 200, pipeline_quality_gate(soft_kolicina=soft_kolicina))
            except Exception as e:
                return api_response(self, 400, {'ok': False, 'error': str(e)})

        if path == '/api/pipeline/health_summary':
            try:
                qs = parse_qs(parsed.query or '')
                soft = (qs.get('soft_kolicina') or ['1'])[0]
                soft_kolicina = (soft != '0')
                return api_response(self, 200, pipeline_health_summary(soft_kolicina=soft_kolicina))
            except Exception as e:
                return api_response(self, 400, {'ok': False, 'error': str(e)})

        if path == '/api/pipeline/batch_detail':
            try:
                qs = parse_qs(parsed.query or '')
                batch = (qs.get('batch') or [''])[0] or '001'
                return api_response(self, 200, pipeline_batch_detail(batch))
            except Exception as e:
                return api_response(self, 400, {'ok': False, 'error': str(e)})

        if path == '/api/pipeline/log':
            try:
                return api_response(self, 200, pipeline_log_read())
            except Exception as e:
                return api_response(self, 400, {'ok': False, 'error': str(e)})

        if path == '/api/pipeline/download':
            try:
                qs = parse_qs(parsed.query or '')
                file_rel = (qs.get('file') or [''])[0]
                if not file_rel:
                    return api_response(self, 400, {'ok': False, 'error': 'Missing file'})
                # allow only within data/pipeline
                ensure_pipeline_paths()
                safe = (PIPELINE_DIR / file_rel).resolve()
                if not str(safe).startswith(str(PIPELINE_DIR.resolve())):
                    return api_response(self, 400, {'ok': False, 'error': 'Not allowed'})
                if not safe.exists() or not safe.is_file():
                    return api_response(self, 404, {'ok': False, 'error': 'File not found'})
                raw = safe.read_bytes()
                ctype = 'application/octet-stream'
                if safe.name.endswith('.json'):
                    ctype = 'application/json; charset=utf-8'
                if safe.name.endswith('.ndjson') or safe.name.endswith('.jsonl') or safe.name.endswith('.txt'):
                    ctype = 'text/plain; charset=utf-8'
                if safe.name.endswith('.zip'):
                    ctype = 'application/zip'
                return _send_bytes(self, raw, safe.name, ctype=ctype)
            except Exception as e:
                return api_response(self, 400, {'ok': False, 'error': str(e)})

        if path.startswith('/api/'):
            return api_response(self, 404, {'ok': False, 'error': 'API endpoint not found (GET)', 'path': path})
        if path == '/':
            self.path = '/index.html'
        return super().do_GET()

    def _read_json_body(self) -> dict:
        try:
            length = int(self.headers.get('Content-Length', '0'))
        except ValueError:
            length = 0
        raw = self.rfile.read(length) if length > 0 else b''
        if not raw:
            return {}
        try:
            return json.loads(raw.decode('utf-8'))
        except json.JSONDecodeError:
            raise ValueError('Invalid JSON body')

    def do_POST(self):
        path = urlparse(self.path).path
        if path == '/api/recipes/import_pdf':
            # multipart/form-data with field name "pdf"
            try:
                try:
                    length = int(self.headers.get('Content-Length', '0'))
                except ValueError:
                    length = 0
                raw = self.rfile.read(length) if length > 0 else b''
                form = parse_multipart_form_bytes(self.headers.get('Content-Type', ''), raw)
                fileitem = form.get('pdf')
                if not fileitem or not fileitem.get('data'):
                    return api_response(self, 400, {'ok': False, 'error': 'Missing field: pdf'})
                pdf_bytes = fileitem.get('data', b'')
                recipe, warnings = recipe_from_pdf_bytes(pdf_bytes)
                return api_response(self, 200, {'ok': True, 'recipe': recipe, 'warnings': warnings})
            except Exception as e:
                return api_response(self, 400, {'ok': False, 'error': str(e)})


        if path == '/api/pipeline/upload_batch':
            try:
                parsed = urlparse(self.path)
                qs = parse_qs(parsed.query or '')
                batch = (qs.get('batch') or [''])[0] or '001'
                # allow multipart file upload OR JSON body text
                ctype = (self.headers.get('Content-Type','') or '').lower()
                if 'multipart/form-data' in ctype:
                    try:
                        length = int(self.headers.get('Content-Length', '0'))
                    except ValueError:
                        length = 0
                    raw = self.rfile.read(length) if length > 0 else b''
                    form = parse_multipart_form_bytes(self.headers.get('Content-Type',''), raw)
                    fi = form.get('file')
                    if not fi or not fi.get('data'):
                        return api_response(self, 400, {'ok': False, 'error': 'Missing field: file'})
                    text = fi.get('data', b'').decode('utf-8', errors='ignore')
                else:
                    body = self._read_json_body()
                    text = str(body.get('text',''))
                if not text.strip():
                    return api_response(self, 400, {'ok': False, 'error': 'Empty text'})
                pipeline_save_batch(batch, text)
                return api_response(self, 200, {'ok': True, 'batch': batch})
            except Exception as e:
                return api_response(self, 400, {'ok': False, 'error': str(e)})

        if path == '/api/pipeline/log_add':
            try:
                body = self._read_json_body()
                batch = str(body.get('batch') or '')
                action = str(body.get('action') or 'manual_note')
                note = str(body.get('note') or '')
                lines = body.get('lines')
                if not note.strip() and action == 'manual_note':
                    return api_response(self, 400, {'ok': False, 'error': 'Empty note'})
                entry = pipeline_log_add(action=action, batch=batch, note=note, lines=(int(lines) if isinstance(lines, int) else None))
                return api_response(self, 200, {'ok': True, 'entry': entry})
            except Exception as e:
                return api_response(self, 400, {'ok': False, 'error': str(e)})

        if path == '/api/pipeline/extract_titles':
            try:
                parsed = urlparse(self.path)
                qs = parse_qs(parsed.query or '')
                batch = (qs.get('batch') or [''])[0] or '001'
                c = pipeline_extract_titles(batch)
                return api_response(self, 200, {'ok': True, 'batch': batch, 'count': c})
            except Exception as e:
                return api_response(self, 400, {'ok': False, 'error': str(e)})

        if path == '/api/pipeline/merge_titles':
            try:
                c = pipeline_merge_titles()
                return api_response(self, 200, {'ok': True, 'count': c})
            except Exception as e:
                return api_response(self, 400, {'ok': False, 'error': str(e)})

        if path == '/api/pipeline/promote_cleaned':
            try:
                body = self._read_json_body()
                batch = str(body.get('batch') or '001')
                keep_backup = bool(body.get('keep_backup', True))
                return api_response(self, 200, pipeline_promote_cleaned(batch=batch, keep_backup=keep_backup))
            except Exception as e:
                return api_response(self, 400, {'ok': False, 'error': str(e)})

        if path == '/api/pipeline/quick_fix':
            try:
                body = self._read_json_body()
                batch = str(body.get('batch') or '001')
                soft_kolicina = bool(body.get('soft_kolicina', True))
                return api_response(self, 200, pipeline_quick_fix(batch=batch, soft_kolicina=soft_kolicina))
            except Exception as e:
                return api_response(self, 400, {'ok': False, 'error': str(e)})

        if path == '/api/pipeline/quick_fix_all':
            try:
                body = self._read_json_body()
                soft_kolicina = bool(body.get('soft_kolicina', True))
                return api_response(self, 200, pipeline_quick_fix_all(soft_kolicina=soft_kolicina))
            except Exception as e:
                return api_response(self, 400, {'ok': False, 'error': str(e)})

        if path == '/api/pipeline/run_merge':
            try:
                body = self._read_json_body()
                autofix = bool(body.get('autofix', True))
                strict = bool(body.get('strict', False))
                soft_kolicina = bool(body.get('soft_kolicina', True))
                use_cleaned = bool(body.get('use_cleaned', False))
                enforce_gate = bool(body.get('enforce_gate', False))
                if enforce_gate:
                    gate = pipeline_quality_gate(soft_kolicina=soft_kolicina)
                    if not gate.get('pass'):
                        pipeline_log_add('quality_gate_blocked', batch='', note=f"Blocked merge. BAD={gate.get('bad_count')}" )
                        return api_response(self, 400, {'ok': False, 'error': 'Quality gate blocked (BAD batches present)', 'gate': gate})
                    else:
                        pipeline_log_add('quality_gate_pass', batch='', note='Quality gate passed')
                stats = pipeline_run_merge(autofix=autofix, strict=strict, soft_kolicina=soft_kolicina, use_cleaned=use_cleaned)
                return api_response(self, 200, {'ok': True, **{k: stats.get(k) for k in ['written_merged','invalid_lines','duplicate_lines']}})
            except Exception as e:
                return api_response(self, 400, {'ok': False, 'error': str(e)})

        if path == '/api/pipeline/atlas_rollback_last':
            try:
                _ = self._read_json_body()  # ignore body
                result = atlas_rollback_last()
                return api_response(self, 200, result)
            except Exception as e:
                return api_response(self, 400, {'ok': False, 'error': str(e)})

        if path == '/api/pipeline/atlas_auto_import':
            try:
                body = self._read_json_body()
                rel_file = str(body.get('file') or 'out/recipes_1000_merged.ndjson')
                make_backup = bool(body.get('backup', True))
                result = pipeline_atlas_auto_import(rel_file=rel_file, make_backup=make_backup)
                return api_response(self, 200, result)
            except Exception as e:
                return api_response(self, 400, {'ok': False, 'error': str(e)})

        if path == '/api/pipeline/export_all':
            try:
                zp = pipeline_export_all_zip()
                rel = str(zp.relative_to(PIPELINE_DIR))
                return api_response(self, 200, {'ok': True, 'file': rel})
            except Exception as e:
                return api_response(self, 400, {'ok': False, 'error': str(e)})

        if not path.startswith('/api/db/'):
            return api_response(self, 404, {'ok': False, 'error': 'API endpoint not found (POST)', 'path': path})

        if path == '/api/db':
            return api_response(self, 405, {'ok': False, 'error': 'Use /api/db/set|remove|merge|backup|import'})

        try:
            body = self._read_json_body()
        except ValueError as e:
            return api_response(self, 400, {'ok': False, 'error': str(e)})

        op = path.split('/api/db/', 1)[1]
        with WRITE_LOCK:
            db = load_db()
            db.setdefault('data', {})
            data = db['data']

            if op == 'set':
                key = str(body.get('key', '')).strip()
                if not key.startswith(ALLOWED_KEY_PREFIX):
                    return api_response(self, 400, {'ok': False, 'error': 'Key not allowed'})
                value = body.get('value', '')
                data[key] = str(value)
                append_event({'ts': utc_now(), 'op': 'set', 'key': key})
                save_db(db)
                return api_response(self, 200, {'ok': True, 'op': 'set', 'key': key})

            if op == 'remove':
                key = str(body.get('key', '')).strip()
                if not key.startswith(ALLOWED_KEY_PREFIX):
                    return api_response(self, 400, {'ok': False, 'error': 'Key not allowed'})
                existed = key in data
                data.pop(key, None)
                append_event({'ts': utc_now(), 'op': 'remove', 'key': key, 'existed': existed})
                save_db(db)
                return api_response(self, 200, {'ok': True, 'op': 'remove', 'key': key, 'existed': existed})

            if op == 'clear_paprikas':
                keys = [k for k in list(data.keys()) if str(k).startswith(ALLOWED_KEY_PREFIX)]
                for k in keys:
                    data.pop(k, None)
                append_event({'ts': utc_now(), 'op': 'clear_paprikas', 'count': len(keys)})
                save_db(db)
                return api_response(self, 200, {'ok': True, 'op': 'clear_paprikas', 'count': len(keys)})

            if op == 'merge':
                incoming = body.get('data')
                if not isinstance(incoming, dict):
                    return api_response(self, 400, {'ok': False, 'error': 'Expected {data:{...}}'})
                changed = 0
                for key, value in incoming.items():
                    key = str(key)
                    if not key.startswith(ALLOWED_KEY_PREFIX):
                        continue
                    data[key] = str(value)
                    changed += 1
                append_event({'ts': utc_now(), 'op': 'merge', 'changed': changed})
                save_db(db)
                return api_response(self, 200, {'ok': True, 'op': 'merge', 'changed': changed})

            if op == 'backup':
                append_event({'ts': utc_now(), 'op': 'backup'})
                save_db(db, make_backup=True)
                return api_response(self, 200, {'ok': True, 'op': 'backup'})

            if op == 'import':
                # Restore from a JSON backup. Safe mode: only keys starting with paprikasHub are applied.
                # Body formats:
                #  - { "db": { "meta": {...}, "data": {...} }, "mode":"replace|merge" }
                #  - { "data": { ... }, "mode":"replace|merge" }
                mode = str(body.get('mode', 'replace')).lower().strip()
                incoming_db = body.get('db')
                incoming_data = None
                incoming_meta = None
                if isinstance(incoming_db, dict):
                    incoming_meta = incoming_db.get('meta') if isinstance(incoming_db.get('meta'), dict) else None
                    incoming_data = incoming_db.get('data') if isinstance(incoming_db.get('data'), dict) else None
                if incoming_data is None and isinstance(body.get('data'), dict):
                    incoming_data = body.get('data')
                if not isinstance(incoming_data, dict):
                    return api_response(self, 400, {'ok': False, 'error': 'Expected {data:{...}} or {db:{meta,data}}'})

                # backup current DB before applying restore
                save_db(db, make_backup=True)

                if mode == 'replace':
                    # clear existing paprikasHub keys first
                    keys = [k for k in list(data.keys()) if str(k).startswith(ALLOWED_KEY_PREFIX)]
                    for k in keys:
                        data.pop(k, None)

                changed = 0
                for key, value in incoming_data.items():
                    key = str(key)
                    if not key.startswith(ALLOWED_KEY_PREFIX):
                        continue
                    data[key] = str(value)
                    changed += 1

                # optionally adopt meta (safe subset)
                if incoming_meta:
                    db.setdefault('meta', {})
                    for mk in ('app', 'db_format'):
                        if mk in incoming_meta:
                            db['meta'][mk] = incoming_meta.get(mk)
                    db['meta']['restored_utc'] = utc_now()

                append_event({'ts': utc_now(), 'op': 'import', 'mode': mode, 'changed': changed})
                save_db(db)
                return api_response(self, 200, {'ok': True, 'op': 'import', 'mode': mode, 'changed': changed})


            return api_response(self, 404, {'ok': False, 'error': f'Unknown op: {op}'})


def main() -> None:
    parser = argparse.ArgumentParser(description='Paprikas Hub local JSON DB server')
    parser.add_argument('--host', default='0.0.0.0')
    parser.add_argument('--port', type=int, default=8015)
    args = parser.parse_args()

    ensure_paths()
    try:
        httpd = ReusableThreadingHTTPServer((args.host, args.port), PaprikasHandler)
    except OSError as e:
        if getattr(e, "errno", None) == 98:
            print(f"❌ Port {args.port} je zauzet. Zaustavi postojeći server ili pokreni drugi port, npr. --port 8016", file=sys.stderr)
            sys.exit(98)
        raise
    print(f"✅ Paprikas Hub server running: http://{args.host}:{args.port}")
    print(f"   UI:   http://127.0.0.1:{args.port}/")
    print(f"   API:  http://127.0.0.1:{args.port}/api/db")
    print(f"   DB:   {DB_FILE}")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n⏹️  Server stopped.")


if __name__ == '__main__':
    main()