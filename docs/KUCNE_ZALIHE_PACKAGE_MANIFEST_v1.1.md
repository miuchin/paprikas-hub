# PACKAGE MANIFEST — KUĆNE ZALIHE MVP OVERLAY v0.1.1

## Tip paketa

Ovo je **overlay paket**.
Ne menja stabilne delove sistema, nego dodaje novi modul u postojeći root:

`paprikas-Hub/`

## Sadržaj paketa

### Dokumentacija
- `docs/KUCNE_ZALIHE_FILE_STORE_PLAN_v1.1.md`
- `docs/KUCNE_ZALIHE_MVP_START_v1.1.md`
- `docs/KUCNE_ZALIHE_PACKAGE_MANIFEST_v1.1.md`

### Seed matrice
- `data/seed/kucne-zalihe/app_matrix_manifest.json`
- `data/seed/kucne-zalihe/food_categories.seed.json`
- `data/seed/kucne-zalihe/units.seed.json`
- `data/seed/kucne-zalihe/default_locations.seed.json`
- `data/seed/kucne-zalihe/food_items.seed.json`
- `data/seed/kucne-zalihe/household_settings.seed.json`

### UI / logika
- `pages/kucne-zalihe.html`
- `pages/iz-frizidera.html`
- `assets/kucne-zalihe.js`
- `assets/kucne-zalihe.css`

## Poravnanje verzije

- dokumentacija: `v1.1`
- modul: `KZ-MVP v0.1.1`
- seed manifest: ostaje kompatibilan sa lokalnim DB slojem `paprikasHubHouseholdV1`

## Stabilni fajlovi nisu menjani

Ovaj paket ne sadrži izmene za:
- `index.html`
- NutriTable fajlove
- postojeći server runtime
- postojeći app state
