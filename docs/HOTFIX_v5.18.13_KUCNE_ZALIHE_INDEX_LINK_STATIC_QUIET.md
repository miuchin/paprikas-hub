# HOTFIX v5.18.13 — KUĆNE ZALIHE INDEX LINK + STATIC QUIET

Datum: 2026-04-06
Root: `paprikas-Hub/`
Tip: additive overlay / safe hotfix

## Šta je ispravljeno

1. **KUĆNE ZALIHE** i **IZ FRIŽIDERA** sada dobijaju vidljive ulazne kartice u glavnom `index.html`.
2. Dodata je i stavka u hamburger meni:
   - Kućne zalihe
   - Iz frižidera
3. U static modu su utišani najglasniji pipeline/status pozivi na Home ekranu kada lokalni API server nije aktivan.
4. Nije dirana NutriTable logika.
5. Nije menjan lokalni KZ data model.
6. Nije uvedena SQL baza.

## Zašto je ranije izgledalo kao greška

Prethodni KZ paketi su bili isporučeni kao **safe overlay** bez izmene glavnog `index.html`, da ne bismo izazvali regresiju stabilnog dela sistema.
Zbog toga su stranice `pages/kucne-zalihe.html` i `pages/iz-frizidera.html` radile same za sebe, ali nisu imale ulaz iz Home-a.

## Šta ovaj hotfix menja

Samo:
- `paprikas-Hub/index.html`
- ovaj dokument u `paprikas-Hub/docs/`

## Test

1. Otvori `index.html`
2. Na Home-u proveri da li vidiš kartice:
   - `Kućne zalihe`
   - `Iz frižidera`
3. Otvori hamburger meni i proveri novu sekciju za KZ modul.
4. Ako radiš bez API servera, Home više ne treba da zatrpava konzolu istim pipeline/status greškama kao ranije.

## Napomena

Ovo je i dalje **safe additive patch**.
Naredni korak može biti zaseban ekran **Nabavka / ulaz robe** uz isti princip.
