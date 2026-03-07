# JNA Clean Import Pipeline (Paprikas Hub)

## Cilj
Bezbedno prebacivanje OCR materijala iz JNA bundle-a u Recipe Atlas, bez šuma iz tabela/nutritivnih delova.

## 3 koraka

### 1) Review (OCR)
- Izvor: `data/catalog/bridges/jna_ocr_bridge_v5.13.9.json`
- Kandidati: prikaz u Biblioteci → JNA OCR modul

### 2) Clean pack (kurirano)
Dva moda:

**A) Bundled Top Clean pack**
- `data/catalog/imports/jna_top_clean_import_v5.15.0.json` / `.ndjson`
- 31 stub recept (naslov + napomena + source_refs)

**B) Draft clean pack (ručno iz UI)**
- Dodavanje: klik `➕ U draft` na kandidatu
- Čuvanje: localStorage `paprikasHubJnaCleanDraftV1`
- Export: JSON/NDJSON

### 3) Import u Recipe Atlas
- 1 klik u JNA panelu (`Import … → Atlas`)
- ili standardni batch import u Recipe Atlas tabu (NDJSON)

## Bezbednosne garancije
- Ne parsiramo OCR tabele i gramaze automatski.
- Svaka stavka ima napomenu + source_refs (TXT/MD/DOCX) za ručnu validaciju.
- Ugrađeni chunk atlas se ne menja; ide u user sloj (localStorage/server DB).

