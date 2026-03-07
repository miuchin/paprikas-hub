# Paprikas Hub v5.14.3 — Library badges & live counts

## Sta je dodato
- dinamicni bedzevi/brojaci za Biblioteku (kolekcije i counts)
- counts se automatski osvezavaju kada se ucitaju bridge JSON fajlovi:
  - Enciklopedija bridge -> broj stavki
  - JNA OCR bridge -> broj naslova i broj citljivijih preview kandidata
- u Home kartici Biblioteka sada stoji mali bedz "2 kolekcije"

## Kako radi
- svi bedzevi koriste `data-ph-count` pa se azuriraju na vise mesta odjednom
- `phLibraryInitCounts()` postavlja staticke brojeve (kolekcije)
- `phLibrarySetCount()` azurira UI kada se bridge ucita
