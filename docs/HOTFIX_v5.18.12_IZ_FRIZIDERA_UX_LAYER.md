# HOTFIX v5.18.12 — IZ FRIŽIDERA UX LAYER

Datum: 2026-04-06
Root: `paprikas-Hub/`
Status: additive overlay, safe patch

## Šta je urađeno

Urađen je UX sloj preko postojeće stranice `pages/iz-frizidera.html` bez izmene NutriTable i bez promene lokalnog data modela.

## Cilj

Da modul bude jasniji za korisnika već na prvom otvaranju:
- brzi izbor horizonta plana
- filteri prikaza predloga
- kartice koje pokazuju tip predloga, procenu vremena, težinu i broj zahvaćenih stavki iz zaliha
- jasan tok rada: stanje -> predlog -> čuvanje -> dopuna

## Bezbednosni okvir

- Bez SQL baze
- Bez izmene stabilne NutriTable logike
- Bez izmene `index.html`
- Bez izmene seed strukture
- Bez izbacivanja postojećih funkcija iz `assets/kucne-zalihe.js`

## Datoteke u ovom overlay paketu

- `paprikas-Hub/pages/iz-frizidera.html`
- `paprikas-Hub/docs/HOTFIX_v5.18.12_IZ_FRIZIDERA_UX_LAYER.md`
- `paprikas-Hub/docs/KUCNE_ZALIHE_UX_REFERENCE_v1.3.md`
- `paprikas-Hub/docs/KUCNE_ZALIHE_TEST_FLOW_v1.3.md`

## Napomena

Ovo je UX poliranje i ne menja source-of-truth pravilo: lokalne zalihe ostaju glavni izvor istine za predlog “Iz frižidera”.
