# KUĆNE ZALIHE / IZ FRIŽIDERA — FILE & STORE PLAN v1.10

Datum: 2026-04-05  
Root folder: `paprikas-Hub/`  
Paket: `KZ-MVP v0.1.2`  
Status: **safe additive overlay / bez diranja stabilnog sistema**

## 1. Zaključane granice

Ovaj korak ostaje unutar tvrdih pravila rada:

- **bez SQL baze**
- **bez diranja NutriTable**
- **bez menjanja stabilnih delova glavnog sistema**
- seed matrice dolaze iz aplikacije / Netlify sloja
- korisnički podaci ostaju lokalni
- root folder ostaje `paprikas-Hub/`
- sva dokumentacija ide u `paprikas-Hub/docs/`

## 2. Šta je novo u v0.1.2

Ovaj korak ne uvodi novu arhitekturu, nego dodaje bezbedniji ulaz u postojeći MVP modul:

- novi start ekran: `pages/kucne-zalihe-start.html`
- poravnata verzija modula na `KZ-MVP v0.1.2`
- poravnati linkovi ka dokumentaciji
- dodat smoke test dokument za lokalnu proveru

## 3. Tačna struktura overlay paketa

### Dokumentacija
- `paprikas-Hub/docs/KUCNE_ZALIHE_FILE_STORE_PLAN_v1.10.md`
- `paprikas-Hub/docs/KUCNE_ZALIHE_MVP_START_v1.10.md`
- `paprikas-Hub/docs/KUCNE_ZALIHE_PACKAGE_MANIFEST_v1.10.md`
- `paprikas-Hub/docs/KUCNE_ZALIHE_SMOKE_TEST_v1.10.md`
- `paprikas-Hub/docs/KUCNE_ZALIHE_NEXT_STEP_v1.10.md`
- `paprikas-Hub/docs/HOTFIX_v5.18.11_KUCNE_ZALIHE_START_HUB.md`

### UI / logika
- `paprikas-Hub/pages/kucne-zalihe-start.html`
- `paprikas-Hub/pages/kucne-zalihe.html`
- `paprikas-Hub/pages/iz-frizidera.html`
- `paprikas-Hub/assets/kucne-zalihe.js`
- `paprikas-Hub/assets/kucne-zalihe.css`

## 4. Store plan

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

## 5. Uloga store-ova u ovom MVP koraku

### Aktivno korišćeni odmah
- `food_items` — read-only izbor namirnica iz kataloga
- `food_categories` — grupisanje i pravila prioriteta
- `units` — mere za unos i prikaz
- `storage_locations` — lokacije po kući
- `stock_entries` — trenutno stanje zaliha
- `inventory_movements` — knjiga ulaza / izlaza / transfera
- `household_settings` — lokalna pravila rada
- `menu_plans_local` — čuvanje generisanog predloga iz modula **Iz frižidera**

### Pripremljeni za sledeći korak
- `purchase_logs`
- `purchase_log_items`
- `menu_plan_reservations`
- `leftover_entries`
- `waste_log`

## 6. Pravilo seed punjenja

Seed se učitava samo kada je lokalni store prazan.
To znači:

- seed ne prepisuje postojeće korisničke podatke
- lokalni rad ostaje privatni
- Netlify / GitHub ostaju isporuka aplikacije i početnih matrica

## 7. Stabilni delovi koji se i dalje ne diraju

Ovaj overlay i dalje **ne menja**:

- glavni nutritivni katalog kao stabilnu celinu
- NutriTable prikaz i sticky logiku
- postojeći server runtime
- postojeći `data/db/app_state.json`
- glavni `index.html`

## 8. Poenta novog START HUB ekrana

Pošto glavni sistem ne diramo, uveden je poseban bezbedan ulaz:

## `pages/kucne-zalihe-start.html`

To omogućava:

- jedan jasan URL za test modula
- brzi skok na **Kućne zalihe**
- brzi skok na **Iz frižidera**
- odmah vidljivu dokumentaciju i smoke test
- nultu regresiju stabilnih delova sistema

## 9. Sledeći razuman korak

Tek kada lokalni test potvrdi da je modul stabilan:

1. opciona integracija u glavni meni
2. modul Nabavka
3. rezervacije za jelovnik
4. ostaci jela / zamrzavanje / odmrzavanje
5. pomoćni foto / QR / barkod ulazi
