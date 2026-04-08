# Paprikas Hub v5.13.6 — Recipes/Open Hotfix

Ovaj hotfix ispravlja tihi problem gde klik na kartice **Recepti** i **Dnevnik** na početnom ekranu nije radio ništa, bez vidljive greške.

## Uzrok
`phOpenCategory()` je otvarao samo grupe menija, ali su neke početne kartice slale **TAB id** (`recipes`, `diary`) umesto id-ja grupe.

## Ispravka
- ako `phOpenCategory()` dobije postojeći TAB id, sada poziva `switchTab(tabId)`
- ako dobije id grupe menija, zadržava staro ponašanje

## Efekat
- **Recepti** sada otvaraju **Recipe Atlas**
- **Dnevnik** sada otvara **Kuhinjski dnevnik**
- server fix za Python 3.13+ i port 8015 ostaju nepromenjeni
