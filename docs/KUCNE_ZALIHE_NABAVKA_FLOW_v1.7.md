# KUĆNE ZALIHE — NABAVKA FLOW v1.7

## Cilj
Treći stub modula: ručni unos nabavke i direktan ulaz robe u lokalne zalihe.

## Ekran
`paprikas-Hub/pages/nabavka.html`

## Minimalni MVP koraci
1. Unos glave nabavke: datum, prodavnica/izvor, tip dokumenta, referenca, ukupno.
2. Dodavanje stavki nabavke samo preko NutriTable/NUTRI_STL izbora.
3. Za svaku stavku: količina, jedinica, lokacija, status, BB/rok, cena, napomena.
4. Potvrda nabavke pravi 4 lokalna efekta:
   - `purchase_logs`
   - `purchase_log_items`
   - `stock_entries`
   - `inventory_movements`
5. Novi ulaz odmah postaje vidljiv u:
   - `pages/kucne-zalihe.html`
   - `pages/iz-frizidera.html`

## Namerno nije rađeno u ovom koraku
- OCR računa
- QR / barkod parser
- automatsko mapiranje slobodnog teksta bez korisničke potvrde
- bilo kakva SQL baza

## Sledeći korak
- dopuna nabavke sa raspodelom po lokacijama i brzim preset-ovima
- povezivanje sa listom za kupovinu iz generatora `Iz frižidera`
