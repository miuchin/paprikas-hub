# HOTFIX v5.18.18 — STATUS LOKALIZACIJA + TERMINALNI IZLAZ + NABAVKA POLIRANJE

Datum: 2026-04-06

## Obuhvat
Overlay paket za Paprikas Hub modul KUĆNE ZALIHE / NABAVKA / IZ FRIŽIDERA.

## Ispravljeno
- UI statusi više ne prikazuju interne kodove poput `sealed`, `opened`, `leftover`
- istorija promena prikazuje lokalizovane tipove pokreta
- terminalni izlaz `Potrošeno` i `Baci` sada upisuju stvarnu količinu u movement log i waste log
- ručni unos zaliha dobija fallback lokaciju ako korisnik ne zada eksplicitnu lokaciju
- Nabavka ekran skraćen je na obavezna polja, dok su batch/rok/napomena prebačeni u "Više opcija"
- poravnati su verzioni stringovi i doc linkovi na v0.1.10 / v1.10

## Fajlovi
- `paprikas-Hub/assets/kucne-zalihe.js`
- `paprikas-Hub/pages/kucne-zalihe.html`
- `paprikas-Hub/pages/nabavka.html`
- `paprikas-Hub/pages/iz-frizidera.html`
- `paprikas-Hub/docs/KUCNE_ZALIHE_FILE_STORE_PLAN_v1.10.md`
- `paprikas-Hub/docs/KUCNE_ZALIHE_NABAVKA_FLOW_v1.10.md`

## Test
1. Ručni unos: izabrati namirnicu, količinu, lokaciju i upisati stavku.
2. Potrošiti jednu stavku i proveriti da je u istoriji negativna količina jednaka stvarnoj količini stavke.
3. Baciti jednu stavku i proveriti `waste_log` kroz backup export.
4. U Nabavci dodati stavku samo sa: namirnica + količina + lokacija.
