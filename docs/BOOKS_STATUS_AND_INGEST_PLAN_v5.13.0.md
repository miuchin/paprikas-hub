# Paprikas Hub books status & ingest plan v5.13.0

Datum: 2026-03-01

## Šta je sada stvarno u paketu

- Osnovni original build sa 1706 recepata je uzet kao baza.
- Batch fajlovi `26–29` su spojeni, uz deduplikaciju po normalizovanom nazivu.
- Novi total u ovom buildu: **1867** recepata.

## Status po izvoru knjiga / tabela

### Čarobna kuhinja #5
- fajl: `arobna-kuhinja-100-recepata-5_compress.pdf`
- strane: **90**
- tekstualna ekstrakcija (prve 3 strane): **4344** karaktera
- tip: **text-pdf**
- najbolji pipeline: **layout-specific recipe parser**

### Srednjovekovni recepti Srbije
- fajl: `kuhinja-naih-predaka-srednjovekovni-recepti-srbije_compress.pdf`
- strane: **32**
- tekstualna ekstrakcija (prve 3 strane): **2331** karaktera
- tip: **text-pdf**
- najbolji pipeline: **heritage pack / curated import**

### PCOS + insulinska + Hashimoto jelovnik
- fajl: `jelovnik-pcos-insulinska-haimoto_compress.pdf`
- strane: **17**
- tekstualna ekstrakcija (prve 3 strane): **6426** karaktera
- tip: **text-pdf**
- najbolji pipeline: **bridge scoring presets / profile guidance**

### GI tabela
- fajl: `glikemijski-indeks-tabela_compress.pdf`
- strane: **4**
- tekstualna ekstrakcija (prve 3 strane): **5236** karaktera
- tip: **text-pdf**
- najbolji pipeline: **nutrition atlas GI/GO layer**

### Kalorijska tabela
- fajl: `kalorijska-tabela_compress.pdf`
- strane: **6**
- tekstualna ekstrakcija (prve 3 strane): **5102** karaktera
- tip: **text-pdf**
- najbolji pipeline: **nutrition atlas kcal/macro review layer**

### Nutritivne tablice
- fajl: `nutritivne-tablice_compress.pdf`
- strane: **39**
- tekstualna ekstrakcija (prve 3 strane): **1703** karaktera
- tip: **text-pdf**
- najbolji pipeline: **nutrition atlas main coverage**

### Normativ za kuvare
- fajl: `normativ-za-kuvare_compress.pdf`
- strane: **48**
- tekstualna ekstrakcija (prve 3 strane): **1543** karaktera
- tip: **text-pdf**
- najbolji pipeline: **quantity/norm parser**

### JNA kuvar
- fajl: `kuvar_jna.pdf`
- strane: **556**
- tekstualna ekstrakcija (prve 3 strane): **0** karaktera
- tip: **scan-heavy**
- najbolji pipeline: **ocr-first segmented cookbook pipeline**

## Šta još nije upečeno u katalog recepata

- PDF knjige i tabele iz gornje liste nisu automatski pretvorene u nove recipe slogove u ovom buildu.
- One su sada **analizirane i klasifikovane**, sa jasnim planom ingest-a po tipu izvora.
- Najbrži sledeći koraci su:
  1. Čarobna kuhinja → parser za isti layout
  2. GI + kalorijske + nutritivne tablice → nutrition atlas merge
  3. Normativ → quantity parser
  4. JNA → OCR round 2+ u segmentima
  5. Srednjovekovna knjiga → heritage pack
