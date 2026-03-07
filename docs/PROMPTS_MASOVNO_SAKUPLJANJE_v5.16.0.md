# Paprikas Hub - Universalni promptovi za sakupljanje sadrzaja (v5.16.0)

## 1) Univerzalni prompt za recepte

Kopiraj ovaj prompt kada zelis 200 / 500 / 1000+ recepata u batch-evima po 100.

:::
TI SI "Recipe generator" za Paprikas Hub.

Generisi tacno {KVOTA} recepata na srpskom jeziku (latinica), bez duplikata.

OBAVEZNO POSTUJ OVA PRAVILA:
- Izlaz mora biti NDJSON (svaki red = 1 JSON objekat)
- Bez uvoda, bez objasnjenja, bez markdown-a
- Ako ne mozes da stanes u jedan odgovor, vrati prvih 100 recepata, a ja cu poslati: CONTINUE
- Svaki sledeci odgovor mora nastaviti tacno gde je prethodni stao
- Ne ponavljaj vec postojece recepte iz liste POSTOJECI_NASLOVI
- Ne izmisljaj prazne recepte: svaki recept mora imati stvarne sastojke i stvarne korake
- Recepti moraju biti upotrebljivi za: import, edit, print, export

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

RASPODELA:
- 35% glavna jela
- 20% corbe/supe/paprikasi
- 15% salate/prilozi
- 15% testa/peciva
- 15% kolaci/deserti

KVALITET:
- Neka nazivi budu raznoliki
- Neka sastojci i koraci budu realni
- Ne ponavljaj isti recept pod drugim imenom

Pocni odmah.
:::

## 2) Prompt za kuhinjske trikove

:::
TI SI "Kitchen tricks generator" za Paprikas Hub.

Generisi tacno {KVOTA} prakticnih kuhinjskih trikova na srpskom jeziku (latinica), bez duplikata.

FORMAT IZLAZA: NDJSON, bez dodatnog teksta. Ako ne stane, vrati prvih 100 pa cekaj CONTINUE.

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

## 3) Prompt za kucne trikove / savete za kucu

:::
TI SI "Home tricks generator" za Paprikas Hub.

Generisi tacno {KVOTA} kratkih i upotrebljivih kucnih trikova na srpskom jeziku (latinica), bez duplikata.

FORMAT IZLAZA: NDJSON, bez dodatnog teksta. Ako ne stane, vrati prvih 100 pa cekaj CONTINUE.

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
