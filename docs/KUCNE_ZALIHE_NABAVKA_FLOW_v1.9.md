# KUĆNE ZALIHE — NABAVKA FLOW v1.10

Datum: 2026-04-06

## Cilj
Pojednostavljen unos nabavke po SINET logici:

1. izaberi namirnicu iz Nutri baze
2. unesi količinu
3. lokacija je obavezna
4. cena je opciona
5. tek na kraju ide završno snimanje cele nabavke

## Šta je polirano u v1.10
- statusi su lokalizovani u UI sloju
- napredna polja za stavku su sklopljena u "Više opcija"
- ručni izlaz "Potrošeno / Baci" sada pravilno upisuje količinski movement log
- fallback lokacija za ručni unos više ne ostavlja tihu praznu lokaciju
- dokumentacioni linkovi su poravnati na v1.10

## Lokalni store tok
- purchase_logs
- purchase_log_items
- stock_entries
- inventory_movements

## Napomena
NutriTable ostaje samo katalog / source za izbor namirnice.
Kućne zalihe ostaju lokalni store sloj.
