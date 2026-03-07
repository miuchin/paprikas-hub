# vv5.18.8 — Auto-backup + Rollback last import

Dodato:
- auto-backup pre svakog Atlas auto-importa (poseban backup tag `atlas-import`)
- import istorija u `data/pipeline/atlas_import_history.json`
- rollback last import (vraća DB iz poslednjeg backup-a)

API:
- GET `/api/pipeline/atlas_import_history?limit=N`
- POST `/api/pipeline/atlas_rollback_last`

Server compile: FAIL:   File "/mnt/data/_paprikas_v5188/paprikas-hub/server/paprikas_server.py", line 1085
    return {
    ^^^^^^^^
SyntaxError: 'return' outside function

