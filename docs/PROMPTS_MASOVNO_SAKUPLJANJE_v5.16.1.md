# Paprikas Hub - universalni promptovi za 1000 recepata (v5.16.1)

## Glavni cilj
- Cilj: **1000 novih recepata**
- Ritam: **do 100 recepata po sesiji**
- Model rada: **sesija 1 -> CONTINUE -> sesija 2 -> CONTINUE** dok se ne popuni svih 1000
- Format: **NDJSON**
- Pravilo: **bez duplikata u odnosu na postojece recepte**

## Fajl koji sluzi za dedup pri generisanju
Koristi ovaj fajl kao listu postojecih naslova:

- `data/exports/recipe_inventory_titles_prompt_ready_v5.16.1.txt`

Ako radis rucno iz chata, nalepi sadrzaj tog TXT fajla u placeholder `POSTOJECI_NASLOVI`.

## 1) Master prompt - 1000 recepata, do 100 po sesiji

:::
TI SI "Recipe generator" za Paprikas Hub.

ZADATAK:
- Generisi ukupno 1000 novih recepata na srpskom jeziku (latinica)
- Vrati najvise 100 recepata u jednoj sesiji
- Kada stanes na 100, cekaj moju poruku: CONTINUE
- Svaki sledeci odgovor mora nastaviti tacno od sledeceg novog recepta, bez ponavljanja prethodnih
- Nemoj ponavljati recepte iz liste POSTOJECI_NASLOVI
- Nemoj ponavljati ni recepte koje si vec generisao u ranijim sesijama

OBAVEZNA PRAVILA:
- Izlaz mora biti cist NDJSON
- Bez uvoda
- Bez objasnjenja
- Bez markdown-a
- Svaki red mora biti 1 validan JSON objekat
- Recept mora biti stvarno upotrebljiv za import, edit, print i export
- Ne izmisljaj prazne ili nepotpune recepte
- Svaki recept mora imati realne sastojke i realne korake

POSTOJECI_NASLOVI:
{OVDE_NALEPI_SPISAK_POSTOJECIH_NASLOVA}

SHEMA SVAKOG JSON OBJEKTA:
{
  "naziv": "...",
  "kategorija": ["...","..."],
  "tags": ["...","..."],
  "porcije": 4,
  "vreme_min": 45,
  "tezina": "lako|srednje|teško",
  "sastojci": [{"item":"...","kolicina":"..."}],
  "koraci": ["...","..."],
  "napomene": "..."
}

RASPODELA PO 1000:
- 300 glavna jela
- 180 corbe, supe i paprikasi
- 150 salate i prilozi
- 150 testa i peciva
- 120 kolaci i deserti
- 100 dorucak i uzina

KVALITET:
- Raznoliki nazivi
- Razliciti glavni sastojci
- Izbegavaj male varijacije istog recepta
- Ne ponavljaj isti recept pod drugim imenom

Sada kreni sa prvih 100 recepata.
:::

## 2) CONTINUE prompt

:::
CONTINUE
Nastavi tacno od sledeceg novog recepta.
Vrati narednih najvise 100 recepata u istom NDJSON formatu.
Ne ponavljaj prethodne recepte i ne vracaj vec postojece naslove.
:::

## 3) Prompt za kuhinjske trikove - 500, do 100 po sesiji

:::
TI SI "Kitchen tricks generator" za Paprikas Hub.

Generisi ukupno 500 prakticnih kuhinjskih trikova na srpskom jeziku (latinica), bez duplikata.
Vrati najvise 100 u jednoj sesiji, pa cekaj CONTINUE.

FORMAT IZLAZA: NDJSON, bez dodatnog teksta.

SHEMA:
{
  "title": "...",
  "group": "ukus|tekstura|organizacija|zamene|odrzavanje",
  "problem": "...",
  "solution": "...",
  "steps": ["...","..."],
  "warning": "...",
  "tags": ["...","..."]
}
:::

## 4) Prompt za kucne trikove - 500, do 100 po sesiji

:::
TI SI "Home tricks generator" za Paprikas Hub.

Generisi ukupno 500 kratkih i upotrebljivih kucnih trikova na srpskom jeziku (latinica), bez duplikata.
Vrati najvise 100 u jednoj sesiji, pa cekaj CONTINUE.

FORMAT IZLAZA: NDJSON, bez dodatnog teksta.

SHEMA:
{
  "title": "...",
  "group": "higijena|mirisi|kamenac|organizacija|pranje|kuhinja|kupatilo",
  "problem": "...",
  "solution": "...",
  "steps": ["...","..."],
  "warning": "...",
  "tags": ["...","..."]
}
:::
