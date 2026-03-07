# Netlify deploy check list

## Varijanta 1 - Drag and drop deploy
1. Preuzmi finalni ZIP paket.
2. Otpakuj ga lokalno i proveri da su u root-u prisutni `index.html`, `pregled.html` i folder `data/`.
3. Otvori Netlify i izaberi **Add new site** ili prevuci otpakovan folder u deploy zonu.
4. Sačekaj da deploy završi.
5. Otvori javni URL i proveri:
   - da se `index.html` učitava
   - da rade interni linkovi
   - da `pregled.html` radi
   - da su JSON fajlovi dostupni
6. Po potrebi promeni naziv sajta.

## Varijanta 2 - GitHub repo povezan sa Netlify
1. Upload paketa u GitHub repo.
2. U Netlify izaberi **Import from Git**.
3. Poveži odgovarajući repozitorijum.
4. Build command ostavi prazno.
5. Publish directory postavi na `.`
6. Pokreni deploy.
7. Proveri javni URL i osnovne stranice.

## Post-deploy provera
- `index.html` otvara glavni prikaz
- `pregled.html` radi ispravno
- `data/structured.json` je dostupan
- `data/sinet_ready_katalog.json` je dostupan
- nema 404 grešaka na internim resursima
- mobilni prikaz je upotrebljiv

## Preporuka
Za prvu objavu najjednostavniji je Netlify drag-and-drop, a za dalji rad i verzionisanje bolji je GitHub + Netlify linked deploy.
