# KUĆNE ZALIHE / IZ FRIŽIDERA — FILE & STORE PLAN v1.0

Datum: 2026-03-27  
Stabilni root: `paprikas-Hub/`  
MVP oznaka modula: `KZ-MVP v0.1.0`

## 1. Tvrde granice

Ovaj paket poštuje sledeće zaključane odluke:

- **nema SQL baze**
- **ne dira se NutriTable**
- **ne menja se stabilni index i postojeći UI tokovi**
- korisnički podaci ostaju **lokalni u browseru**
- seed matrice dolaze iz aplikacije / Netlify sloja
- novi modul živi kao **poseban dodatni sloj** koji kasnije može bezbedno da se poveže na glavni meni

## 2. Predložena struktura fajlova

### Novi docs fajlovi
- `paprikas-Hub/docs/KUCNE_ZALIHE_FILE_STORE_PLAN_v1.0.md`
- `paprikas-Hub/docs/KUCNE_ZALIHE_MVP_START_v1.0.md`
- `paprikas-Hub/docs/KUCNE_ZALIHE_PACKAGE_MANIFEST_v1.0.md`

### Novi seed fajlovi
- `paprikas-Hub/data/seed/kucne-zalihe/app_matrix_manifest.json`
- `paprikas-Hub/data/seed/kucne-zalihe/food_categories.seed.json`
- `paprikas-Hub/data/seed/kucne-zalihe/units.seed.json`
- `paprikas-Hub/data/seed/kucne-zalihe/default_locations.seed.json`
- `paprikas-Hub/data/seed/kucne-zalihe/food_items.seed.json`
- `paprikas-Hub/data/seed/kucne-zalihe/household_settings.seed.json`

### Novi UI fajlovi
- `paprikas-Hub/pages/kucne-zalihe.html`
- `paprikas-Hub/pages/iz-frizidera.html`
- `paprikas-Hub/assets/kucne-zalihe.js`
- `paprikas-Hub/assets/kucne-zalihe.css`

## 3. Konkretnan store plan za MVP

MVP koristi **IndexedDB** kao lokalni store sloj, zato što:

- nije SQL baza
- ne zavisi od servera
- ostaje lokalno kod korisnika
- bolji je za strukturirane kolekcije od običnog LocalStorage-a
- lakše podržava kasniji rast modula

### Baza
- DB ime: `paprikasHubHouseholdV1`
- Schema version: `1`

### Store-ovi

#### Seed / katalog sloj
1. `food_items`
2. `food_categories`
3. `units`

#### Lokalni korisnički sloj
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

## 4. Šta je stvarno uključeno u ovom MVP paketu

### Aktivno radi
- inicijalno punjenje seed matrica
- lokalne lokacije u kući
- ručni unos zaliha
- pregled aktivnih zaliha
- osnovni ulaz/izlaz log
- brzi dashboard sa prioritetima
- eksport lokalne baze u JSON
- import lokalne baze iz JSON backupa
- posebna stranica **Iz frižidera** sa prioritet listom i predlozima obroka

### Namerno ostavljeno za naredni korak
- OCR računa
- QR / barkod ulaz
- potpuno automatsko mapiranje sa Nutri katalogom
- automatsko skidanje izlaza pri potvrdi kompleksnog jelovnika
- napredne rezervacije po danima
- višekorisnički sloj

## 5. Pravilo seed matrica

Seed podaci dolaze iz `data/seed/kucne-zalihe/`.

MVP radi ovako:

- ako je store prazan, puni se iz seed fajlova
- ako korisnik već ima lokalne podatke, seed se **ne prepisuje preko njih**
- za `food_items` MVP prvo učitava mali lokalni seed, a zatim po potrebi može da pročita postojeći katalog iz projekta samo kao **read-only pomoćni seed**

## 6. Odnos prema postojećem sistemu

### Ne diramo
- `index.html`
- NutriTable modul
- postojeći sticky prikaz i stabilnu nutritivnu logiku
- postojeći `data/db/app_state.json`

### Novi modul živi pored toga
- korisnik može direktno da otvori `pages/kucne-zalihe.html`
- korisnik može direktno da otvori `pages/iz-frizidera.html`
- kasnije se može dodati link iz glavnog menija, ali to **nije deo ovog bezbednog MVP koraka**

## 7. Preporučeni naredni korak posle ovog paketa

1. vizuelno povezivanje na glavni meni bez regresije
2. dopuna modula Nabavka
3. rezervacije za jelovnik
4. potvrda izlaza iz zaliha posle obroka
5. ostaci jela / zamrzavanje / odmrzavanje
6. pomoćni ulazi foto račun / QR / barkod
