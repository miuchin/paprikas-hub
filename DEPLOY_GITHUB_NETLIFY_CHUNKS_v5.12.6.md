# Deploy notes — GitHub / Netlify / chunked catalog

## GitHub
Za veliki projekat **nemoj web upload** hiljada fajlova. Koristi:
- GitHub Desktop, ili
- `git` CLI

Ovaj build je pripremljen tako da recepti nisu hiljade malih fajlova, već:
- 1 manifest
- 9 chunk JSON fajlova

## Netlify
Najzdraviji model za ovaj projekat je:
- statički deploy aplikacije
- chunked JSON katalog kao asset
- opcioni offline cache kasnije

Ne preporučuje se browser unzip tok za iPhone/Safari kao primarni deploy model.

## Loader model
Aplikacija prvo pokušava:
- `data/recipes_chunks/manifest.json`

Ako chunk katalog nije prisutan, koristi legacy fallback na:
- `data/recipes/index.json`

## Trenutni katalog
- ukupno recepata: **1711**
- chunk size: **200**
- broj chunk fajlova: **9**
