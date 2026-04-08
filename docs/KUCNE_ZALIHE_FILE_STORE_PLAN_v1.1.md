# KUĆNE ZALIHE / IZ FRIŽIDERA — FILE & STORE PLAN v1.1

Datum: 2026-04-05  
Root folder: `paprikas-Hub/`  
Paket: `KZ-MVP v0.1.1`  
Status: **safe additive overlay**

## 1. Zaključane granice

Ovaj plan poštuje tvrda pravila rada:

- **bez SQL baze**
- **bez diranja NutriTable**
- **bez menjanja stabilnih delova sistema**
- seed matrice dolaze iz aplikacije / Netlify sloja
- korisnički podaci ostaju lokalni
- root folder ostaje `paprikas-Hub/`
- sva dokumentacija ide u `paprikas-Hub/docs/`

## 2. Tačna struktura MVP overlay paketa

### Dokumentacija
- `paprikas-Hub/docs/KUCNE_ZALIHE_FILE_STORE_PLAN_v1.1.md`
- `paprikas-Hub/docs/KUCNE_ZALIHE_MVP_START_v1.1.md`
- `paprikas-Hub/docs/KUCNE_ZALIHE_PACKAGE_MANIFEST_v1.1.md`

### Seed matrice
- `paprikas-Hub/data/seed/kucne-zalihe/app_matrix_manifest.json`
- `paprikas-Hub/data/seed/kucne-zalihe/food_categories.seed.json`
- `paprikas-Hub/data/seed/kucne-zalihe/units.seed.json`
- `paprikas-Hub/data/seed/kucne-zalihe/default_locations.seed.json`
- `paprikas-Hub/data/seed/kucne-zalihe/food_items.seed.json`
- `paprikas-Hub/data/seed/kucne-zalihe/household_settings.seed.json`

### UI / logika
- `paprikas-Hub/pages/kucne-zalihe.html`
- `paprikas-Hub/pages/iz-frizidera.html`
- `paprikas-Hub/assets/kucne-zalihe.js`
- `paprikas-Hub/assets/kucne-zalihe.css`

## 3. Store plan

MVP koristi **IndexedDB** kao lokalni korisnički store.

### DB identitet
- DB ime: `paprikasHubHouseholdV1`
- schema version: `1`

### Seed / katalog store-ovi
1. `food_items`
2. `food_categories`
3. `units`

### Lokalni korisnički store-ovi
4. `storage_locations`
5. `stock_entries`
6. `inventory_movements`
7. `purchase_logs`
8. `purchase_log_items`
9. `menu_plan_reservations`
10. `menu_plans_local`
11. `leftover_entries`
12. `waste_log`
13. `household_settings`

## 4. Uloga svakog store-a u MVP-u

### Aktivno korišćeni odmah
- `food_items` — osnovni izbor namirnica i pomoćni katalog
- `food_categories` — grupisanje i pravila prioriteta
- `units` — mere za unos i prikaz
- `storage_locations` — lokacije po kući
- `stock_entries` — trenutno stanje zaliha
- `inventory_movements` — knjiga ulaza / izlaza / transfera
- `household_settings` — lokalna pravila rada
- `menu_plans_local` — čuvanje generisanog predloga iz modula **Iz frižidera**

### Pripremljeni za sledeću fazu
- `purchase_logs`
- `purchase_log_items`
- `menu_plan_reservations`
- `leftover_entries`
- `waste_log`

## 5. Pravilo punjenja seed matrica

MVP puni seed podatke samo kada je lokalni store prazan.
To znači:

- seed ne prepisuje postojeće korisničke podatke
- korisnik može da nastavi rad lokalno bez zavisnosti od servera
- Netlify / GitHub ostaju sloj za isporuku aplikacije i početnih matrica

## 6. Stabilni delovi koji se ne diraju

Ovaj overlay **ne menja**:

- glavni `index.html`
- NutriTable prikaz i sticky logiku
- postojeći nutritivni katalog kao stabilnu celinu
- postojeći `data/db/app_state.json`
- server sloj koji već radi

## 7. MVP funkcionalni opseg

### Uključeno
- inicijalni seed import
- pregled lokacija
- dodavanje novih lokacija
- ručni unos zaliha
- aktivna tabela stanja
- osnovni terminalni izlaz (`meal_out`, `waste_out`)
- istorija promena
- export / import lokalne baze u JSON
- generator **Iz frižidera**
- lokalno čuvanje predloga plana

### Namerno odloženo
- OCR računa
- QR / barkod ulaz
- automatsko skidanje svih rezervacija iz složenog jelovnika
- puna nabavka sa mapiranjem cena i računa
- dublja veza sa stabilnim glavnim menijem

## 8. Preporučeni redosled sledećih faza

1. bezbedno povezivanje na glavni meni
2. modul Nabavka
3. rezervacije za jelovnik
4. ostaci jela / zamrzavanje / odmrzavanje
5. pomoćni foto / QR / barkod ulazi

## 9. Napomena o verziji

U starijoj dokumentaciji ostao je trag `v0.1.0`, dok su stranice i JS već na `v0.1.1`.
U ovom planu sve je poravnato na:

## `KZ-MVP v0.1.1`
