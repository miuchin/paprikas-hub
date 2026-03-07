# Paprikas Hub - status audit (v5.16.0)

## Stvarno stanje
- Recipe Atlas katalog postoji i ima 1773 recepta u 10 chunk fajlova.
- Batch import za JSON / NDJSON / CSV / TXT postoji u UI-u.
- PDF import server endpoint postoji, ali UI funkcije za PDF import su falile i zato taj tok nije bio zavrsen.
- Postoje moduli za kuhinjske trikove, kucne trikove i fleke/mirise.
- Ne postoji poseban folder sa gotovim univerzalnim promptovima za masovno sakupljanje recepata - to je sada dopunjeno u docs.
- Ne postoji gotov inventory export naslova recepata za dedup pri novom sakupljanju - to je sada dopunjeno u data/exports.

## Sadrzaj modula
- kitchen_tricks_v48: 18 trikova
- home_tricks_v48: 12 trikova
- stains_odors_rescue_v48: 18 stavki

## Prioritetni zakljucak
Glavni fokus vise ne treba da bude JNA, vec: 
1. masovno sakupljanje novih recepata bez duplikata
2. cist import tok
3. inventory postojece baze
4. kasnije prosirenje trikova i saveta za kucu
