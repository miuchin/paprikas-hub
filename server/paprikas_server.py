#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Paprikas Hub local server (static files + JSON DB API).

- Serves index.html and all static files from project root
- Persists browser state immediately into data/db/app_state.json
- Uses append-only events log + atomic file writes
"""
from __future__ import annotations

import argparse
import cgi
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
from urllib.parse import urlparse

import pdfplumber

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data" / "db"
DB_FILE = DATA_DIR / "app_state.json"
EVENTS_FILE = DATA_DIR / "events.ndjson"
BACKUP_DIR = DATA_DIR / "backups"
WRITE_LOCK = Lock()
ALLOWED_KEY_PREFIX = "paprikasHub"


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
        path = urlparse(self.path).path
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
                ctype, pdict = cgi.parse_header(self.headers.get('content-type', ''))
                if ctype != 'multipart/form-data':
                    return api_response(self, 400, {'ok': False, 'error': 'Expected multipart/form-data'})
                pdict['boundary'] = pdict['boundary'].encode('utf-8') if isinstance(pdict.get('boundary'), str) else pdict.get('boundary')
                form = cgi.FieldStorage(fp=self.rfile, headers=self.headers, environ={'REQUEST_METHOD':'POST','CONTENT_TYPE': self.headers.get('Content-Type',''), 'CONTENT_LENGTH': self.headers.get('Content-Length','0')})
                fileitem = form['pdf'] if 'pdf' in form else None
                if not fileitem or not getattr(fileitem, 'file', None):
                    return api_response(self, 400, {'ok': False, 'error': 'Missing field: pdf'})
                pdf_bytes = fileitem.file.read()
                recipe, warnings = recipe_from_pdf_bytes(pdf_bytes)
                return api_response(self, 200, {'ok': True, 'recipe': recipe, 'warnings': warnings})
            except Exception as e:
                return api_response(self, 400, {'ok': False, 'error': str(e)})

        if not path.startswith('/api/db/'):
            return api_response(self, 404, {'ok': False, 'error': 'API endpoint not found'})

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
