# vv5.18.4 — Quality gate (pre-merge)

- Dodato: Quality gate (blokira merge ako postoje BAD batch-evi)
- UI: checkbox `Quality gate`, dugme `🛡️ Gate check`, i `🚦 Fix→Gate→Merge`
- API: `GET /api/pipeline/quality_gate` + server-side enforce u `run_merge` ako `enforce_gate=true`

Server compile: OK
