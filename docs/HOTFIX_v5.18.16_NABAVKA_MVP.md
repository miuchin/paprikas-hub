# HOTFIX v5.18.16 — KUĆNE ZALIHE / NABAVKA MVP

Datum: 2026-04-06
Root: `paprikas-Hub/`

## Šta je dodato
- novi ekran `pages/nabavka.html`
- proširen lokalni store sloj u `assets/kucne-zalihe.js`
- linkovi ka Nabavci iz `index.html`, `pages/kucne-zalihe.html` i `pages/iz-frizidera.html`

## Novi lokalni tok
`manual purchase head` + `purchase items` → `purchase_logs` + `purchase_log_items` → `stock_entries` + `inventory_movements`

## Pravila koja ostaju netaknuta
- bez SQL baze
- bez diranja NutriTable prikaza
- korisnički podaci ostaju lokalni
- seed matrice ostaju u aplikaciji / Netlify sloju

## Smoke test
1. Otvoriti `index.html`
2. Kliknuti karticu **Nabavka**
3. Dodati 2 stavke iz NutriTable liste
4. Sačuvati nabavku
5. Proveriti da li se stavke vide u `Kućne zalihe`
6. Proveriti da li je `Iz frižidera` odmah vidi u prioritetima / planu
