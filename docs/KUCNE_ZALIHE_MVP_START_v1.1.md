# KUĆNE ZALIHE / IZ FRIŽIDERA — MVP START v1.1

## Otvaranje

Za prvi test ne diraj stabilne delove sistema. Otvori direktno:

- `pages/kucne-zalihe.html`
- `pages/iz-frizidera.html`

## Prvi test scenario

1. Podigni lokalni server iz root foldera `paprikas-Hub/`
2. Otvori `pages/kucne-zalihe.html`
3. Proveri da li su seed lokacije i jedinice mere učitane
4. Dodaj 2–3 svoje lokacije
5. Unesi nekoliko stvarnih zaliha
6. Proveri dashboard, tabelu i istoriju promena
7. Uradi **Izvoz lokalne baze** i sačuvaj JSON backup
8. Otvori `pages/iz-frizidera.html`
9. Generiši predlog za 1 obrok i 3 dana
10. Sačuvaj predlog lokalno

## Cilj ovog MVP koraka

- potvrda arhitekture
- tačan file/store plan
- rad bez SQL baze
- rad bez diranja NutriTable
- lokalna privatnost korisničkih podataka
- siguran dodatni modul bez regresije

## Nije cilj ovog koraka

- potpuna integracija u glavni meni
- puna nabavka sa računima
- OCR / QR / barkod
- finalna rezervacija za kompleksne jelovnike

## Obavezan radni običaj

Pošto su podaci lokalni u browseru, radi redovan JSON export backupa.
