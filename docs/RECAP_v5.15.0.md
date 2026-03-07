# Paprikas Hub v5.15.0 — Rekapitulacija (Novi Chat nastavak)

Datum: 2026-03-02

## Potvrđeni uslovi
- Isporuka: **pun kod u ZIP**
- Lokalni server: **8015**
- Python: **3.13+**
- UI: responsive / mobile-first
- Dokumentacija: **MD**

## Šta je dodato u v5.15.0

### 1) JNA Top Clean import pack (bezbedan)
Generisani fajlovi (bundled u projektu):

- `data/catalog/imports/jna_top_clean_import_v5.15.0.json`
- `data/catalog/imports/jna_top_clean_import_v5.15.0.ndjson`
- `data/catalog/imports/jna_top_clean_summary_v5.15.0.json`

Pack sadrži **31 'clean stub'** recept (naslov + kategorija guess + napomene + source_refs),
bez auto-parsiranja OCR tabela/gramaža.

Generator:
- `tools/build_jna_top_clean_import.py`

### 2) Tok u UI: review → clean import → Recipe Atlas
U JNA biblioteci dodat je blok **🧼 JNA → Clean import → Recipe Atlas** sa:
- učitavanjem Top Clean pack-a
- 1-klik importom u Recipe Atlas (kao **user** recepti)
- draft clean pack (localStorage) + export (JSON/NDJSON) + import u Atlas

### 3) Verzionisanje na vrhu index.html
Stari statički string `v5.8.3 • SINET Light` je zamenjen tako da se vidi tekuća verzija:
- `PH_APP_VERSION = "v5.15.0"`
- `<span id="phVersionTag">…</span>` u headeru

### 4) Python 3.13+ kompatibilnost: pdfplumber opcioni
U `server/paprikas_server.py`:
- `pdfplumber` je sada **optional import**
- ako nije instaliran, PDF import ruta vraća jasnu grešku, a server radi normalno

### 5) One-click start fajlovi
Dodato:
- `requirements.txt`
- `start.sh`
- `start_windows.bat`

## Kako se startuje

### Linux / Manjaro
```bash
cd paprikas-hub
./start.sh 8015
# otvori: http://127.0.0.1:8015/
```

### Windows
Dvoklik: `start_windows.bat` (podrazumevano 8015)

## Napomena za import
- Import Top Clean pack-a dodaje stavke u **tvoje recepte** (user), ne menja ugrađene chunk fajlove.
- Ako želiš batch import preko postojećeg dugmeta, koristi `jna_top_clean_import_v5.15.0.ndjson`.

