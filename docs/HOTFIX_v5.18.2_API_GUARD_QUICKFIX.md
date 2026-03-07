# HOTFIX v5.18.2 — API guard + Quick fix

## Šta je ispravljeno
- GET nepoznati `/api/*` više ne padaju na HTML 404 stranicu, već vraćaju JSON grešku:
  - `API endpoint not found (GET)`
- POST nepoznati `/api/*` vraćaju JSON grešku:
  - `API endpoint not found (POST)`

Ovo uklanja greške tipa:
- `Unexpected token '<'`
- `<!DOCTYPE ... is not valid JSON`

## Šta je dodato
- **Quick fix batch**
  - `POST /api/pipeline/quick_fix`
  - pravi:
    - `batch-XYZ.cleaned.ndjson`
    - `batch-XYZ.invalid.ndjson`
- UI dugmad:
  - `🛠️ Quick fix batch`
  - `⬇️ Download cleaned`

## Važno
Ako si prethodno pokrenuo stariji server proces, moraš ga potpuno ugasiti i ponovo pokrenuti, jer stari proces ostaje u memoriji i nastavlja da koristi staru route mapu.

Server compile: OK
