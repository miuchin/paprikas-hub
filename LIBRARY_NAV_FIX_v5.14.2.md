# Paprikas Hub v5.14.2 — Library nav / toggle fix

## Ispravke
- uklonjen inline `ontoggle` poziv koji je mogao da okine pre nego što globalna funkcija bude dostupna
- dodata `phLibraryInitBindings()` inicijalizacija nakon `DOMContentLoaded`
- "Sadržaj Biblioteke" ostavljen je prvi u rasporedu, a uvodna kartica je spuštena u glavni sadržaj
- zadržan accordion model za Enciklopediju i JNA bundle

## Efekat
- nema više `phLibrarySyncNav is not defined` pri otvaranju Biblioteke
- korisnik odmah vidi da Biblioteka sadrži više kolekcija
