# vv5.18.5 — Auto recheck loop

- Dodato: `phPipelineRecheckAll(reason)` koji automatski osvežava:
  - pipeline status
  - home dashboard
  - batch detail
  - session log
  - next-step panel
- Recheck se automatski pokreće nakon:
  - Quick fix ALL
  - Quick fix batch
  - Promote cleaned
  - Merge
  - startup

Server compile: OK
