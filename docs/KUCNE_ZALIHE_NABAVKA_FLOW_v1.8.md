# KUĆNE ZALIHE — NABAVKA FLOW v1.8

## Cilj
Nabavka mora da bude brza i jasna:
- izbor namirnice iz Nutri baze
- količina kao obavezna vrednost
- cena kao opciona vrednost
- kraj unosa kao jedinstvena potvrda cele nabavke

## Ekran
`paprikas-Hub/pages/nabavka.html`

## Usvojeni jednostavni tok
1. Unesi osnovu nabavke: datum, izvor/prodavnica, podrazumevana lokacija.
2. U polju `Namirnica iz Nutri baze` izaberi tačnu stavku iz kataloga.
3. Unesi količinu.
4. Po potrebi koriguj jedinicu, lokaciju, status ili cenu.
5. Klikni `Dodaj stavku u listu`.
6. Kada završiš sve stavke, klikni `Završi unos i upiši u Kućne zalihe`.

## Lokalni efekti potvrde
Jedna potvrđena nabavka pravi lokalne upise u:
- `purchase_logs`
- `purchase_log_items`
- `stock_entries`
- `inventory_movements`

## Obavezno ponašanje MVP-a
- namirnica mora biti izabrana iz Nutri baze
- količina mora biti > 0
- cena je opciona
- lokacija se bira ručno ili preuzima iz podrazumevane lokacije / fallback lokacije
- novi ulaz odmah mora biti vidljiv u `Kućne zalihe` i dostupan modulu `Iz frižidera`

## Namerno nije rađeno u ovom koraku
- OCR računa
- QR / barkod parser
- automatsko slobodno mapiranje bez potvrde
- bilo kakva SQL baza

## Sledeći korak
- preset dugmad za često korišćene lokacije
- dopuna iz shopping hints / plana iz modula `Iz frižidera`
- brzi unos `dodaj istu stavku još jednom`
