# Enciklopedija narodnih metoda lečenja - README (SR)

Digitalno i responsive HTML izdanje knjige **Enciklopedija narodnih metoda lečenja**, pripremljeno za čitanje u pregledaču i za objavu preko **GitHub Pages** ili **Netlify**.

## Autorstvo
- **Svetozar Miuchin (miuchins)**
- **OpenAI ChatGPT**

## Sadržaj paketa
- `index.html` - glavni prikaz knjige
- `pregled.html` - pregled poglavlja i brzi ulaz
- `data/structured.json` - strukturirani izlaz knjige
- `data/sinet_ready_katalog.json` - kurirani SINET katalog
- `data/oblasti/` - podaci grupisani po oblastima
- `data/tipovi/` - podaci grupisani po tipovima
- `data/review_candidates.json` - preostale stavke za mogući ručni review
- `source/enciklopedija_narodnih_metoda_lecenja_original.pdf` - originalni izvor
- prateća dokumentacija za deploy, release i nastavak rada

## Funkcionalnosti
- responsive prikaz za desktop i mobilne uređaje
- navigacija kroz poglavlja
- pregled strukture knjige
- JSON izvoz za dalju obradu
- SINET-ready katalog za buduću integraciju
- static hosting friendly struktura bez build koraka

## Trenutno stanje kataloga
- recepti / protokoli: 50
- biljke i namirnice: 59
- tegobe: 29
- opšti saveti: 9

## Lokalno pokretanje
Dovoljno je otvoriti `index.html` u pregledaču. Za hosting, ceo sadržaj foldera može da ide direktno u root statičkog sajta.

## GitHub Pages
1. Kreiraj repozitorijum.
2. Uploaduj ceo sadržaj paketa u root.
3. Commit i push.
4. Uključi GitHub Pages.
5. Kao source koristi root folder odgovarajuće grane.

## Netlify
- Build command: nije potreban
- Publish directory: `.`
- `netlify.toml` je već uključen

## Napomena
Ovaj release je regenerisan iz sačuvanih stabilnih artefakata, kako bi ponovo bio dostupan za preuzimanje nakon isteka sesije.
