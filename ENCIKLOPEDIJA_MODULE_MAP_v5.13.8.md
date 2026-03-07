# Enciklopedija -> Paprikas Hub / SINET module map (v5.13.8)

## Sažetak

Iz knjige **Enciklopedija narodnih metoda lečenja** je prepoznato ukupno **147** kuriranih stavki:

- biljke i namirnice: **59**
- opšti saveti: **9**
- recepti i protokoli: **50**
- tegobe: **29**

## Šta ide gde

| Cilj | Modul | Stavke sada | Status | Upotreba sada | Sledeći korak |
|---|---|---:|---|---|---|
| Paprikas Hub | Biblioteka / Enciklopedija | 147 | Implementirano | Read-only pregled, pretraga, otvaranje originalne HTML knjige | Ostaje kao referentni viewer |
| Paprikas Hub | Seed za atlas biljaka i namirnica | 59 | Implementirano | Data fajl za budući ingredient atlas / traditional notes | Ručni merge sa nutri atlasom |
| Paprikas Hub | Opšti saveti kao pomoćna referenca | 9 | Implementirano | Pregled bez automatskog preporučivanja | Ručna validacija pre dubljeg povezivanja |
| SINET | Katalog narodnih metoda | 147 | Implementirano kao export bridge | Sirovina za review/import tok | Mapiranje po oblastima i red flags |
| SINET | Review queue za protokole i tegobe | 79 | Implementirano kao export bridge | Odvojeno za kasniji medicinsko-informativni review | Fino mapiranje na SINET model |

## Pravilo bezbedne upotrebe

- **Paprikas Hub**: sadržaj je referentni i ne ulazi direktno u Recipe Atlas niti daje automatske medicinske preporuke.
- **SINET**: sadržaj je pripremljen kao review/import bridge i treba da prođe ručnu i tematsku proveru.

## Implementirano u buildu

- novi TAB: **Biblioteka / Enciklopedija**
- home launcher kartica za Biblioteku
- meni kategorija za Biblioteku
- ugrađena HTML knjiga u `references/enciklopedija_narodnih_metoda/`
- bridge JSON:
  - `data/catalog/bridges/enciklopedija_narodnih_metoda_bridge_v5.13.8.json`
- seed za Paprikas ingredient sloj:
  - `data/catalog/ingredient_traditional_seed_from_enciklopedija_v5.13.8.json`
- SINET bridge export:
  - `data/catalog/sinet_traditional_bridge_from_enciklopedija_v5.13.8.json`

## Primeri relevantni za Paprikas Hub

- Aloja (sok od aloje)
- Anis
- Anis (Pimpinela anisum)
- Beli glog
- Borovnica
- Bunika
- Cmiluk
- Crni i beli luk
- Crvena borovnica
- Crvena cvekla
- Cvetovi različka
- Grozničica

## Primeri relevantni za SINET

- Akupresura
- Bol u ušima
- Bolesti očiju
- Bolovi u predelu lakatnog zgloba
- Bolovi u predelu uha
- Bolovi u predelu zgloba kolena
- Bolovi u žučnoj kesi (kolike)
- Crveni vetar
- Dijabetes
- Disajni organi
- Diuretici - 1. Zova
- Glaukom
