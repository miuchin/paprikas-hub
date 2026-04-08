# KUĆNE ZALIHE / IZ FRIŽIDERA — UX REFERENCE v1.3

Datum: 2026-04-06
Root: `paprikas-Hub/`

## Osnovna ideja

UX sloj treba da korisniku odmah odgovori na četiri pitanja:

1. Šta mogu da spremim sada?
2. Šta prvo treba da potrošim?
3. Da li da planiram samo jedan obrok ili nekoliko dana?
4. Šta će mi posle toga faliti za dopunu?

## Princip

Paprikaš Hub ostaje **inventory-first** sistem.
To znači da se UX može približiti “upiši šta imaš” iskustvu, ali ne sme da zameni stvarno stanje kućnih zaliha.

## Šta je ugrađeno u v1.3

- hero početak sa 4 jasne akcije
- quick horizon dugmad
- filteri: Sve / Potroši prvo / Brzo / Lako / Doručak-užina / Za više dana
- bogatije kartice predloga
- jasniji tok rada ispod glavnog modula

## Šta nije dirano

- NutriTable stabilni sloj
- lokalni store model
- seed matrice
- glavna početna strana

## Sledeći UX korak

Ako test prođe dobro, sledeći bezbedan korak je:
- dodati karticu “IZ FRIŽIDERA” na postojeći home/dashboard tok
- dodati lakši prelaz iz `kucne-zalihe.html` u generator sa unapred zadržanim kontekstom
