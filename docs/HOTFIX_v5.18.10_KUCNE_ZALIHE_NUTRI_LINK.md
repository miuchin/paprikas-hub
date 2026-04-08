# HOTFIX v5.18.10 — KUĆNE ZALIHE / NUTRI LINK

Datum: 2026-03-28
Root: `paprikas-Hub/`

## Šta je promenjeno
- naziv namirnice u Kućnim zalihama više se bira iz NutriTable kataloga
- izvor za izbor je kanonski `data/NUTRI_STL.json`
- nakon izbora automatski se pune:
  - naziv
  - Nutri grupa
  - kategorija za kućne zalihe
  - podrazumevana jedinica za unos
  - Nutri ref / snapshot
- ručni slobodan unos naziva je isključen za ovaj ekran

## Napomena o jedinici
Nutri kanon je pre svega nutritivni katalog po 100g i ne sadrži uvek direktnu kućnu jedinicu za zalihu.
Zato modul koristi podrazumevanu jedinicu za kućni unos po pravilima (npr. jaja=kom, mleko/jogurt=ml, ostalo najčešće=g), uz mogućnost ručne izmene pre upisa.

## Važno
- NutriTable prikaz nije diran
- stabilni delovi sistema nisu menjani
- veza je read-only prema Nutri katalogu
- korisnički podaci ostaju lokalni
