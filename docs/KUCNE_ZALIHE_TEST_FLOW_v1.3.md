# KUĆNE ZALIHE — TEST FLOW v1.3

Datum: 2026-04-06
Root: `paprikas-Hub/`

## Lokalni smoke test

1. Otvoriti `pages/kucne-zalihe.html`
2. Proveriti da li seed lokacije i katalozi postoje
3. Uneti 3–5 realnih stavki u zalihu
4. Otvoriti `pages/iz-frizidera.html`
5. Kliknuti:
   - `Predloži sada`
   - `Planiraj 3 dana`
   - `Pokaži prioritet`
6. Proveriti da li filteri menjaju prikaz kartica
7. Kliknuti `Sačuvaj predlog`
8. Proveriti da li nema JavaScript grešaka u konzoli

## Test scenario A — ostatci + otvoreno pakovanje

Predlog stanja:
- kuvani krompir / ostatak jela
- jogurt / otvoreno
- paprika
- jaja
- hleb

Očekivanje:
- kartica “Prvo potroši ostatke”
- kartica za otvorena pakovanja
- brzi doručak ili lagani obrok

## Test scenario B — 3 dana

Predlog stanja:
- pirinač
- testenina
- šargarepa
- luk
- piletina
- smrznuti grašak

Očekivanje:
- glavni obrok / tiganj / wok
- predlog za više dana
- razumna dopuna ako proteina ili povrća nema dovoljno

## Test scenario C — prazna zaliha

Očekivanje:
- jasan empty state
- bez pucanja stranice
- bez lažnih predloga
