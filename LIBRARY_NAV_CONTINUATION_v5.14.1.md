# Paprikas Hub v5.14.1 - Library Navigation Continuation

Ova iteracija nastavlja plan iz v5.14.0 i fokusira se na preglednost taba **Biblioteka**.

## Sta je dodato

- leva / sticky mini navigacija **Sadrzaj Biblioteke**
- jasne kartice za svaku kolekciju
- dugmad:
  - **Samo naslovi**
  - **Otvori sve**
- aktivna sekcija je vizuelno oznacena
- klik na stavku u sadrzaju:
  - otvara trazenu knjigu
  - zatvara ostale sekcije
  - skroluje do izabrane sekcije
- `details` sekcije sada sinhronizuju aktivnu stavku u navigaciji

## Zasto je ovo bitno

Korisnik sada odmah vidi da Biblioteka sadrzi vise kolekcija:

- Enciklopedija narodnih metoda
- Kuvar JNA - OCR bundle review

To uklanja problem "beskonacnog skrola" i cini strukturu biblioteke citljivijom na prvi pogled.

## Tehnicki status

- Python 3.13+ server fix ostaje aktivan
- localhost port ostaje **8015**
- Recipe Atlas baza ostaje netaknuta
- potvrden servis: `/api/ping`

## Potvrden katalog u ovom buildu

- recepti: **1773**
- chunk fajlovi: **10**

## Sledeci preporuceni korak

- dodati mali brojac / bedz na glavnoj pocetnoj kartici Biblioteka
- po zelji ubaciti i trecu kolekciju kada stigne novi izvor
- zatim nastaviti na **JNA Top Clean import pack**
