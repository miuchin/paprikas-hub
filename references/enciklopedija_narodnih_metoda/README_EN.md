# Encyclopedia of Traditional Healing Methods - README (EN)

A digital, responsive HTML edition of the book **Enciklopedija narodnih metoda lecenja**, prepared for browser reading and deployment through **GitHub Pages** or **Netlify**.

## Credits
- **Svetozar Miuchin (miuchins)**
- **OpenAI ChatGPT**

## Package contents
- `index.html` - main reading interface
- `pregled.html` - chapter overview and quick navigation
- `data/structured.json` - structured book output
- `data/sinet_ready_katalog.json` - curated SINET catalog
- `data/oblasti/` - topic-based data subsets
- `data/tipovi/` - type-based data subsets
- `data/review_candidates.json` - remaining items for possible manual review
- `source/enciklopedija_narodnih_metoda_lecenja_original.pdf` - original PDF source
- supporting docs for deployment, release, and project continuation

## Features
- responsive layout for desktop and mobile
- chapter-based navigation
- structured book overview
- JSON outputs for downstream processing
- SINET-ready dataset for future integration
- static hosting friendly structure with no build step required

## Current catalog snapshot
- recipes / protocols: 50
- plants and ingredients: 59
- conditions / symptoms: 29
- general advice entries: 9

## Local usage
Open `index.html` in a browser. For hosting, place the full package in the root of a static site.

## GitHub Pages
1. Create a repository.
2. Upload the full package to the repository root.
3. Commit and push.
4. Enable GitHub Pages.
5. Use the root folder of the selected branch as the source.

## Netlify
- Build command: not required
- Publish directory: `.`
- `netlify.toml` is already included

## Note
This release package was regenerated from stable artifacts preserved in the current session so it can be downloaded again after the previous session expired.
