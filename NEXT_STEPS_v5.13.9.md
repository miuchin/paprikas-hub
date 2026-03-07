# NEXT STEPS v5.13.9

## 1) JNA OCR normalizacija - prioritet
- iz `safe_preview` skupa izvuci prvo najčistije recepte
- fokus:
  - supe i čorbe
  - gulaši / variva
  - prilozi
  - testa / pite / kolači
- za svaki kandidat:
  - očisti naslov
  - rekonstruiši korake
  - ingredient tabelu vrati ručno / poluručno

## 2) Duplikati
- proveri exact overlap listu od 20 naslova
- ne uvoziti ih automatski
- za njih radi samo:
  - kvalitetniji opis
  - ili bolju varijantu ako JNA verzija ima posebnu vrednost

## 3) Put ka Recipe Atlas-u
- tek kada recept ima:
  - čist naziv
  - sastojke
  - razumljive korake
  - porciju / vreme makar približno
- tada ga prebaciti u standardni recipe JSON

## 4) Sledeći build
- JNA Top Clean import pack
- jedan mali, strogo kuriran paket najčistijih JNA recepata
- pa zatim novi FULL ZIP
