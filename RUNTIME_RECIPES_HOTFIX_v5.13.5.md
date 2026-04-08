# Paprikas Hub v5.13.5 - runtime + recipes hotfix

## Sta je uradjeno
- Zadrzan Python 3.13+ server fix bez `cgi` modula.
- Zadrzan Recipe Atlas JS hotfix iz v5.13.4.
- Ugradjen uploadovani `recipes_chunks.zip` paket.
- Ispravljen zastareo `manifest.json` koji je prijavljivao samo 1706 recepata i 9 chunk fajlova.
- Detektovan i ukljucen `recipes-part-010.json`.
- `recipes-part-010.json` normalizovan na isti format kao ostali chunk fajlovi (`{part,count,recipes}`).

## Novi rezultat
- Ukupno recepata u chunk katalogu: **1773**
- Ukupno chunk fajlova: **10**
- Lokalni server: **http://127.0.0.1:8015/**

## Pokretanje
```bash
cd paprikas-hub
./start.sh
```

ili

```bash
./scripts/start_paprikas_server.sh 8015
```

## Napomena
Ovaj paket ne potvrđuje ranije pomenutih 1991 recepata, jer takav izvorni ZIP nije bio dostupan u ovom chatu. Iskoriscen je jedini pronadjeni paket chunk fajlova, a stvarno prisutan sadrzaj je korigovan i ukljucen u manifest.
