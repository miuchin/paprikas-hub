# Paprikas Hub v5.13.9 - JNA OCR Bridge

## Šta je urađeno
- dodat **JNA OCR read-only bridge** u okviru taba **Biblioteka**
- bundle `kuvar_jna_ocr_bundle.zip` je raspakovan i ugrađen offline u projekat
- dodata lokalna referenca na:
  - `references/jna_kuvar_ocr/kuvar_jna_ocr.txt`
  - `references/jna_kuvar_ocr/kuvar_jna_ocr.md`
  - `references/jna_kuvar_ocr/kuvar_jna_ocr.docx`
  - `references/jna_kuvar_ocr/kuvar_jna_ocr_bundle.zip`
- generisan bridge JSON:
  - `data/catalog/bridges/jna_ocr_bridge_v5.13.9.json`
  - `data/catalog/bridges/jna_ocr_review_export_v5.13.9.json`

## Ključni zaključak
JNA OCR bundle je **dovoljno dobar za bezbedan read-only import u Biblioteku**, ali **nije još bezbedan za direktan auto-import u Recipe Atlas**.

## Šta sada može bezbedno
- naslovni indeks recepata
- OCR preview pripreme
- pretraga po naslovu i preview tekstu
- filter:
  - čitljiviji preview
  - review red
  - unique vs Atlas
  - exact overlap
  - kategorije

## Šta je blokirano za auto-merge
- tačne gramaze iz OCR tabela
- nutritivne i zaštitne vrednosti
- randmani / porcije kada su vezani za šumovite tabele
- tihi direktni import u glavni Recipe Atlas

## Rezultat iz bundle-a
- indeksirano naslova: **328**
- čitljiviji OCR preview kandidati: **270**
- review-only kandidati: **58**
- exact overlap sa Recipe Atlas-om: **20**
- jedinstveni naslovi vs Recipe Atlas: **308**

## Gde u UI
- otvori **Biblioteka**
- u okviru taba sada postoji kartica:
  - **Kuvar JNA - OCR bundle review**

## Predlog za sledeći korak
1. zadrži JNA sada kao **Biblioteka + review queue**
2. zatim radi **normalizaciju sastojaka i koraka** samo nad najboljim kandidatima
3. tek posle toga idi na **merge u Recipe Atlas**
