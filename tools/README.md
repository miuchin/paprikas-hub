# Tools (Paprikaš Hub)

Ovo su pomoćni skriptovi za batch rad (za korisnike koji imaju mnogo PDF kuvara / recepata).

## pdf_batch_import.py
**Batch import** recepata iz foldera sa PDF fajlovima u `data/recipes/*.json` i automatski update `data/recipes/index.json`.

Primer:
```bash
python3 tools/pdf_batch_import.py /putanja/do/pdfs --limit 20
```

Napomena:
- Radi najbolje na PDF-ovima koji imaju selektabilan tekst (ne scan).
- Svaki PDF se tretira kao **jedan recept** (best-effort). Posle u aplikaciji možeš da ga doteraš u Editor-u.
