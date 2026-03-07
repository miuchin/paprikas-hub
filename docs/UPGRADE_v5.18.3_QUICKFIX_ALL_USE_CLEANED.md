# vv5.18.3 — Quick fix ALL + Use cleaned + Promote cleaned

## Novo
- Content Studio:
  - `🛠️ Quick fix ALL` (popravlja sve batch-eve koji postoje)
  - opcija `Use cleaned` (merge koristi `batch-XYZ.cleaned.ndjson` ako postoji)
- Batch detail:
  - `⬇️ Download invalid` (preuzmi invalid linije)
  - `✅ Promote cleaned` (cleaned → raw, pravi .bak)
- API:
  - `POST /api/pipeline/quick_fix_all`
  - `POST /api/pipeline/promote_cleaned`
  - `run_merge` prima `use_cleaned`

Server compile: OK
