# Paprikaš Hub v5.4 SINET Light (Kitchen Rescue + Recipe Atlas)



## Nova mogućnost u v5.4
- 📦 Ugrađen **Batch #3** (`recepti-75.json`) — **45 novih recepata**.
- 📚 Ukupno ugrađenih recepata sada: **104** (inkl. svi prethodni batch-evi).
- 🧾 Exporti: `data/exports/recepti_batch_3_45.(json|ndjson)` i `recepti_all_104.(json|ndjson)`.
## Nova mogućnost u v5.3
- 📖 Recipe Atlas: Export **HTML DETALJNO**, **JSON**, **NDJSON**, **CSV**, **TXT**
- 📥 Batch import: **JSON/NDJSON/CSV/TXT**
- 📄 PDF import (server-only) za brzi unos pojedinačnih recepata

## Pokretanje (server + DB na disku)
```bash
python3 server/paprikas_server.py --host 127.0.0.1 --port 8015
```
UI: `http://127.0.0.1:8015/`

✅ Jedan HTML fajl (offline), bez build alata.

## Šta ima u v3.7
- TAB: **Detaljno FULL**
- TAB: **Metode & alternative**
- TAB: **Mini hitna pomoć**
- TAB: **A4 + Decision Tree** (print)
- TAB: **Kalkulator** (ljutina; copy/export + istorija)
- TAB: **Kuhinjski dnevnik** (export MD/TXT)
- TAB: **Batch rescue** (podela lonca / etapno vraćanje)
- TAB: **Serving mod** (po tanjiru / profil osobe)
- TAB: **Zagorelo Rescue**
- TAB: **Preslano Rescue**
- TAB: **Preslatko Rescue**
- TAB: **Bljutavo Rescue** ✨
- TAB: **Prekiselo Rescue** 🍋
- TAB: **Pregusto / Preretko Rescue** 🥣
- TAB: **Premasno Rescue** 🛢️
- TAB: **Gorko Rescue** 🌫️
- TAB: **Mere & Tajming** (konverter + planer serviranja) 📏⏱️
- TAB: **Kuhinjski Rescue Atlas** (master indeks + print navigacija) 🗺️

- TAB: **Čuvanje & podgrevanje** (food safety helper) 🥶
- TAB: **Odmrzavanje helper** (plan + tajming) 🧊
- TAB: **Leftover Rescue / sutrašnji obrok** 🥡
- TAB: **“Šta da kuvam od onoga što imam” mini planer** 🧠
- TAB: **Pametna kupovina / zamene namirnica** 🛒
- TAB: **Meal prep planer (1–3 dana)** 📅
- TAB: **Budžet kuvanje helper** 💸
- TAB: **Organizacija kuhinje / manje pranja sudova** 🧼
- TAB: **Korisničko uputstvo (detaljno)** 📖
- Dodat MD dokument: **KORISNICKO_UPUTSTVO_DETALJNO.md**

## Kako pokrenuti
1. Otvori `paprikas-hub-tabs-v3.7-full.html` u browseru.
2. Sve radi lokalno (offline).
3. Podaci (istorija/dnevnik) se čuvaju u `localStorage`.

## Napomena
Kalkulatori daju **orijentacione** predloge. Uvek radi korekcije u malim koracima i probaj između koraka.

## Novo u ovoj verziji (v3.7)
- Dodati novi praktični moduli:
  - **🛒 Pametna kupovina / zamene namirnica**
  - **📅 Meal prep planer (1–3 dana)**
  - **💸 Budžet kuvanje helper**
  - **🧼 Organizacija kuhinje / redosled rada / manje pranja sudova**
- Prošireno **detaljno Korisničko uputstvo** (novi moduli + kako da se koriste korak-po-korak)
- Dodata arhitekturna napomena / plan za prelaz na **data-first** organizaciju (JSON + baza + server)
- Proširena navigacija (toolbar + TAB-ovi)
- Tehnički: novi `localStorage` ključevi (`V37`) radi čistog prelaza verzije

---

## v3.8 Data-first (JSON baza na disku + lokalni server)

### Glavni fajl
- `index.html` (preimenovan iz prethodnog HTML-a)

### Brzi start (preporučeno — sa upisom u JSON bazu)
```bash
cd /home/miuchins/Desktop/SINET/paprikas-Hub
./scripts/start_paprikas_server.sh
```
Otvori: `http://127.0.0.1:8015`

### Samo statički preview (bez upisa u server bazu)
```bash
cd /home/miuchins/Desktop/SINET/paprikas-Hub
./scripts/start_static_preview_8015.sh
```

### Instalacija/raspored foldera (Manjaro/Linux)
Ako si raspakovao ovaj paket bilo gde, pokreni:
```bash
cd <raspakovan-v3.8-folder>
./scripts/setup_paprikas_hub_manjaro.sh
```

### JSON baza
- `data/db/app_state.json` — glavni state
- `data/db/events.ndjson` — log promena
- `data/db/backups/` — backup snapshoti

> Napomena: `python3 -m http.server 8015` ne može da prima POST upise. Za **odmah upis u bazu** koristi `start_paprikas_server.sh`.


## Važno: dve vrste pokretanja (UI vs API)

### 1) Statički preview (samo UI)
```bash
python3 -m http.server 8015
```
- Radi: `http://localhost:8015/index.html`
- **Ne radi**: `/api/db` (404 je normalno), jer ovo nije API server.

### 2) Full lokalni server (UI + JSON baza + API)
```bash
./scripts/start_paprikas_server.sh
```
- Radi UI: `http://127.0.0.1:8015/`
- Radi API: `http://127.0.0.1:8015/api/ping`
- Radi API: `http://127.0.0.1:8015/api/db`

## Gde su dokumenta
Sva dokumenta (MD/JSON) su u folderu `docs/`, osim `README.md` koji ostaje u root-u.

## Troubleshooting (No such file or directory)
Ako dobiješ:
```bash
./scripts/setup_paprikas_hub_manjaro.sh: No such file or directory
```
znači da:
- nisi u root folderu raspakovanog paketa, ili
- ZIP nije raspakovan kako treba.

Provera:
```bash
pwd
ls -la
ls -la scripts
```
U root folderu treba da vidiš: `index.html`, `server/`, `scripts/`, `data/`, `docs/`.
