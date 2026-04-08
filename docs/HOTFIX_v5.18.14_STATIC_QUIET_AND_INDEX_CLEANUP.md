# HOTFIX v5.18.14 — STATIC QUIET + INDEX CLEANUP

Datum: 2026-04-06
Root: `paprikas-Hub/`

## Šta je ispravljeno

Ovaj hotfix rešava problem sa velikim brojem crvenih grešaka u F12 konzoli kada se Paprikas Hub otvara preko običnog statičkog servera (`python -m http.server`, port 8004 i slično), dok FULL lokalni API server nije aktivan.

### Glavne ispravke
- uveden je **auto STATIC detect** za lokalne preview portove i statičke deploy-e
- uveden je **quiet fetch stub** za same-origin `/api/*` pozive u STATIC modu
- `Home dashboard` više ne radi raw `/api/pipeline/*` pozive kada API nije aktivan
- startup tok više ne pravi lavinu 404 + `Unexpected token '<'` poruka u konzoli
- glavni `index.html` i dalje sadrži ulaze za **Kućne zalihe** i **Iz frižidera**

## Važno pravilo

- FULL server: preporučen port `8015`, alternativno `8016`
- STATIC preview: bilo koji drugi port (`8004`, `8000`, Netlify preview...) tretira se kao static mode
- ako korisnik ipak želi API ponašanje na nestandardnom portu, može da doda `?api=1`

Primeri:
- static preview: `http://127.0.0.1:8004/index.html`
- forced static: `http://127.0.0.1:8004/index.html?static=1`
- forced api mode: `http://127.0.0.1:8004/index.html?api=1`

## Nije dirano
- NutriTable
- lokalni KZ data model
- seed matrice
- stabilni sadržaj van `index.html`
