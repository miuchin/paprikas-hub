# Content Studio (vv5.17.0)

Ovaj panel u **Recipe Atlas** tabu objedinjuje kompletan workflow za **1000 novih recepata (10×100)**:

- Copy prompt za izabrani batch
- paste NDJSON u textarea i snimi u server (batches folder)
- Extract titles (za dedup)
- Merge titles → `all-previous-titles.txt`
- Auto-fix + Merge → `recipes_1000_merged.ndjson`
- Download merged + reports zip
- Export ALL (backup zip)

## Gde se fajlovi čuvaju
Server čuva sve u:
`data/pipeline/`

- `data/pipeline/batches/batch-001..010.ndjson`
- `data/pipeline/titles/batch-001-titles.txt` + `all-previous-titles.txt`
- `data/pipeline/out/recipes_1000_merged.ndjson` + report + invalid + duplicates + reports_bundle.zip

## Soft accept (prazna kolicina)
U merge opcijama ima checkbox **Soft accept prazna kolicina**.
Ako je uključeno, recepti sa praznom `kolicina` prolaze, ali ostaju normalizovani.

## Start
```bash
python3 server/paprikas_server.py --port 8015
# otvori http://127.0.0.1:8015/
```
