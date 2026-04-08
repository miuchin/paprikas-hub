# HOTFIX v5.18.15 — STATIC CONSOLE CLEAN

Datum: 2026-04-06

## Šta je ispravljeno
- očekivani pipeline/static warning više se ne ispisuje u F12 konzoli kada je aplikacija svesno otvorena u STATIC modu
- ostaju UI poruke unutar stranice da API/pipeline nisu aktivni
- linkovi za Kućne zalihe i Iz frižidera ostaju u glavnom index-u

## Važno
Ovo nije gašenje pravih grešaka. Utišan je samo očekivani warning u scenariju kada aplikacija radi preko običnog static servera bez API sloja.
