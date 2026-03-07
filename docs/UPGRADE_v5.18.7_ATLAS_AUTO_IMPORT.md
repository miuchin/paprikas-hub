# vv5.18.7 — Atlas auto-import (server + UI)

Dodato: Auto-import merged NDJSON u Recipe Atlas bez ručnog biranja fajla.

## API
- `POST /api/pipeline/atlas_auto_import` body: `{file:'out/recipes_1000_merged.ndjson', backup:true}`
- Server:
  - čita pipeline merged fajl
  - normalizuje recepte
  - merge-uje u DB key `paprikasHubRecipesUserV1`
  - pravi backup DB pre upisa

## UI
- Finalize 1000 sada automatski radi i auto-import.
- Dodat ručni taster `⚡ Auto-import u Atlas` pored Download merged.

Server compile: OK
