# KUĆNE ZALIHE / IZ FRIŽIDERA — MVP START v1.0

## Otvaranje

Bez diranja stabilnih delova sistema, za prvi pregled otvori:

- `pages/kucne-zalihe.html`
- `pages/iz-frizidera.html`

## Šta prvo testirati

1. Otvori `pages/kucne-zalihe.html`
2. Proveri da li su učitane početne lokacije i jedinice mere
3. Dodaj 2–3 lokacije po svojoj kući
4. Unesi nekoliko zaliha ručno
5. Proveri dashboard i tabelu stanja
6. Klikni na **Izvoz lokalne baze** i sačuvaj JSON
7. Otvori `pages/iz-frizidera.html`
8. Generiši predlog za 1 obrok i 3 dana

## Šta je cilj MVP-a

- da arhitektura bude tačna
- da file/store plan bude konkretan
- da modul radi odvojeno od NutriTable
- da korisnički podaci ostaju lokalni
- da seed matrice dolaze iz aplikacije

## Šta nije cilj ovog prvog koraka

- finalna integracija u glavni meni
- OCR i barkod
- automatsko skidanje izlaza iz složenih jelovnika
- puna nabavka sa računima

## Napomena o lokalnim podacima

MVP čuva korisničke podatke u IndexedDB bazi preglednika.
To znači da su podaci vezani za taj browser/profil dok se ne uradi export backup.

Zato je dugme **Izvoz lokalne baze** obavezni deo rada.
