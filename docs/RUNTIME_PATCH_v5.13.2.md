# Paprikas Hub v5.13.2 — Runtime patch

## Šta je ispravljeno
- server više ne koristi `cgi`, pa radi i na Python 3.13+
- FULL lokalni server ostaje na portu `8015`
- dodat API proxy `GET /api/recipes/fetch_json?url=...` za učitavanje udaljenog JSON kataloga preko lokalnog servera

## Šta je dodato u UI
- u **Recipe Atlas** toolbar:
  - `🔄 Osveži bazu`
  - `🧼 Cache`
- u **Backup / Restore** prozor:
  - polje za **Spoljni URL kataloga** (npr. Netlify root)
  - `💾 Sačuvaj izvor`
  - `↩️ Vrati na lokalni izvor`
  - `🔄 Osveži bazu recepata`
  - `🧼 Obriši browser cache`
- info linija sa izvorom kataloga, brojem recepata, chunk count, verzijom i vremenom generisanja manifesta

## Kako se koristi
1. Za lokalni FULL mod pokreni `./start.sh 8015`
2. Ako želiš da lokalni build vuče katalog sa Netlify sajta, u Settings upiši root URL sajta
3. Klikni `🔄 Osveži bazu recepata`
4. Ako browser i dalje drži staro stanje, klikni `🧼 Obriši browser cache`

## Napomena
Uploadovani ZIP koji je analiziran trenutno sadrži `1706` recepata u `data/recipes_chunks/manifest.json`.
Ako želiš da lokalni build vidi više od toga, moraš ili:
- ubaciti noviji manifest/chunk fajlove u projekat, ili
- upisati noviji Netlify URL kao spoljni izvor kataloga.
