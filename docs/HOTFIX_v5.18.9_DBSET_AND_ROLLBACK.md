# HOTFIX v5.18.9

## Fix 1 — /api/db/set 404
- `POST /api/db/set` je vraćao 404 jer je POST API-guard presekao sve `/api/*` rute pre DB handlera.
- Sada guard propušta `/api/db/*`.

## Fix 2 — server SyntaxError u v5.18.8
- Ispravljen je pogrešan indent `return` u `pipeline_atlas_auto_import`.
- Uklonjen je dupli `"backup"` ključ u import history entry.

## Brza provera
- `http://localhost:8015/api/ping` → `{"ok": true, ...}`
- U F12 više ne sme da postoji: `POST /api/db/set 404`
