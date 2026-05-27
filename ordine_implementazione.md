Ordine di scrittura del codice che suggerisco
Seguire esattamente la Fase 1 della roadmap, in questo ordine preciso:
1. Struttura cartelle e file vuoti
Creare tutto lo scheletro del progetto con file __init__.py vuoti e commenti. Così gli import funzionano subito e non ci sono sorprese dopo.
2. config.yaml + lettura config
Il primo file vero. Tutto il codice successivo lo usa.
3. Database — models.py + database.py
Definire le tabelle SQLAlchemy. Verificare che SQLite si crei correttamente.
4. Un fetcher solo — Greenhouse
Il più semplice, API pubblica pura. Verificare che restituisce dati nel formato standard definito nella sezione 15.
5. Normalizzatore base
Solo per Greenhouse per ora. Verificare che i dati entrano nel database correttamente.
6. JobSpy adapter
LinkedIn + Indeed in una riga. Verificare normalizzazione e salvataggio.
7. Search engine — orchestratore
Connette fetcher → normalizzatore → deduplicatore → database.
8. Streamlit — scheletro UI
Login + scheda Risultati con tabella base. I dati ci sono già nel DB a questo punto.
9. Scheduler
Per ultimo — solo quando tutto il resto funziona.