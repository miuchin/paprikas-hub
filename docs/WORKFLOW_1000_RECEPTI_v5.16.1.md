# Paprikas Hub - workflow za 1000 novih recepata (v5.16.1)

## Cilj
Napraviti **1000 novih recepata** bez duplikata u odnosu na postojecu bazu, u ritmu **do 100 recepata po sesiji**.

## Ulazni fajl za dedup
- `data/exports/recipe_inventory_titles_prompt_ready_v5.16.1.txt`

## Praktican redosled rada
1. Otvori `prompts/recipes_1000_session_100_v5.16.1.txt`
2. U placeholder `POSTOJECI_NASLOVI` nalepi sadrzaj fajla `data/exports/recipe_inventory_titles_prompt_ready_v5.16.1.txt`
3. Posalji prompt i preuzmi prvih 100 recepata
4. Sacuvaj izlaz kao `batch-001.ndjson`
5. Posalji `prompts/recipes_continue_v5.16.1.txt`
6. Sacuvaj sledeci izlaz kao `batch-002.ndjson`
7. Nastavi do `batch-010.ndjson`
8. Validiraj i deduplikuj batch fajlove pre importa
9. Importuj finalni pack u Recipe Atlas

## Preporuceni nazivi batch fajlova
- `batch-001.ndjson`
- `batch-002.ndjson`
- `batch-003.ndjson`
- `batch-004.ndjson`
- `batch-005.ndjson`
- `batch-006.ndjson`
- `batch-007.ndjson`
- `batch-008.ndjson`
- `batch-009.ndjson`
- `batch-010.ndjson`

## Validacija i priprema import pack-a
Ako batch fajlove drzis lokalno, koristi postojece alate projekta:

```bash
python3 tools/web_collect_validator.py batch-*.ndjson --out validated_1000.ndjson --format ndjson --source-name "recipe-generator" --source-note "1000 recipes / 10 sessions"
python3 tools/web_collect_pipeline.py validated_1000.ndjson --out-dir build_collect_1000 --title recipe_collect_1000_v5_16_1 --source-name "recipe-generator" --source-note "1000 recipes / 10 sessions" --against data/recipes_chunks/recipes-part-001.json data/recipes_chunks/recipes-part-002.json data/recipes_chunks/recipes-part-003.json data/recipes_chunks/recipes-part-004.json data/recipes_chunks/recipes-part-005.json data/recipes_chunks/recipes-part-006.json data/recipes_chunks/recipes-part-007.json data/recipes_chunks/recipes-part-008.json data/recipes_chunks/recipes-part-009.json data/recipes_chunks/recipes-part-010.json
```

## Sta dobijas na kraju
- jedan validiran i deduplikovan import pack
- jasan report koliko je novih recepata proslo
- manje gubljenja vremena na recepte koje vec imas
