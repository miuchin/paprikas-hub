# NEXT STEPS v5.13.8

## Odmah dostupno
- Otvori TAB **Biblioteka**
- Testiraj pretragu i filtere
- Otvori originalnu knjigu i pregled poglavlja iz aplikacije
- Proveri `data/catalog/ingredient_traditional_seed_from_enciklopedija_v5.13.8.json`
- Proveri `data/catalog/sinet_traditional_bridge_from_enciklopedija_v5.13.8.json`

## Sledeći realni merge koraci
1. JNA original PDF + OCR/searchable PDF
2. poređenje JNA ekstrakcije sa postojećih 1773 recepata
3. dedup / merge u recipe katalog
4. poseban merge pass za ingredient atlas:
   - ingredient_nutri_seed_enriched_v5.12.8.json
   - ingredient_traditional_seed_from_enciklopedija_v5.13.8.json
5. SINET review pass:
   - protokoli
   - tegobe
   - biljke / namirnice
   - opšti saveti

## Pravilo
- Paprikas Hub = biblioteka + ingredient bridge
- SINET = review-gated import tok
