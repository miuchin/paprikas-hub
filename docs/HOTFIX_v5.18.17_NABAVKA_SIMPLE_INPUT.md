# HOTFIX v5.18.17 — KUĆNE ZALIHE / NABAVKA SIMPLE INPUT

Datum: 2026-04-06  
Root: `paprikas-Hub/`

## Razlog izmene
Prethodni Nabavka MVP ekran bio je funkcionalan, ali korisniku nije bio dovoljno jasan za svakodnevni rad.
Novi pravac je uprošćen po uzoru na jednostavan unos iz SINET ERP / kućni troškovi obrasca:
- jedan jasan unos stavke
- dodavanje u privremenu listu
- završetak unosa tek na kraju
- cena ostaje opciona

## Šta je promenjeno
- `pages/nabavka.html` je preuređen u jednostavan tok unosa
- više nema zbunjujućeg starta sa više praznih redova
- uvedena je jasna sekvenca:
  1. osnovni podaci nabavke
  2. odabir namirnice iz Nutri baze
  3. količina + jedinica + lokacija
  4. dodaj u listu
  5. završi unos i upiši u Kućne zalihe
- `assets/kucne-zalihe.js` sada kod nabavke uzima i prvu aktivnu lokaciju kao fallback ako lokacija nije eksplicitno prosleđena

## Šta ostaje isto
- bez SQL baze
- bez diranja NutriTable prikaza
- korisnički podaci ostaju lokalni
- Nabavka ostaje poseban modul pored NutriTable

## Smoke test
1. Otvoriti `pages/nabavka.html`
2. Uneti datum i izvor nabavke
3. Izabrati namirnicu iz Nutri baze
4. Uneti količinu
5. Kliknuti `Dodaj stavku u listu`
6. Ponoviti za još 1–2 stavke
7. Kliknuti `Završi unos i upiši u Kućne zalihe`
8. Proveriti u `pages/kucne-zalihe.html` da li se novi ulazi vide odmah
9. Proveriti u `pages/iz-frizidera.html` da li su nove stavke dostupne za predloge
