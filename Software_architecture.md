# Job Finder — Documento di Architettura

## 1. Obiettivo

Applicazione web multi-utente in Python per aggregare annunci di lavoro da più sorgenti, normalizzarli in un formato unico, filtrarli e tracciarli in una dashboard con stato delle candidature.

Pensata inizialmente per due profili utente, con potenziale di espansione a nuovi utenti e settori:
- **Software Engineer** (ricerca tecnica, remote-friendly, stack-based)
- **Geopolitica / Relazioni Internazionali** (ONG, think tank, istituzioni internazionali)

---

## 2. Stack Tecnologico

| Componente | Scelta | Motivazione |
|---|---|---|
| Linguaggio | Python 3.11+ | Ecosistema ricco, librerie HTTP mature |
| UI | Streamlit | Tutto in Python, nessun frontend separato, hostabile |
| Database | PostgreSQL | Server-side, multi-utente, gestito da Railway |
| ORM | SQLAlchemy | Stessa interfaccia di SQLite in sviluppo, PostgreSQL in produzione |
| HTTP client | `httpx` | Async-ready, moderno |
| Scraping alto livello | `python-jobspy` | Copre LinkedIn, Indeed, Glassdoor, Google, ZipRecruiter con una riga di codice |
| Browser automation | `Playwright` | Mantenuto da Microsoft. Per siti pubblici JS-heavy non coperti da JobSpy (Idealist, Eurobrussels, Wellfound). Fondamentale per il profilo geopolitica. |
| Autenticazione | `streamlit-authenticator` | Login utente semplice, configurabile via YAML |
| Hosting | Railway | Supporta Python, PostgreSQL nativo, Playwright, deploy automatico da GitHub |
| Parsing JSON | built-in `json` | Sufficiente per le API dirette |
| Scheduling | `APScheduler` | Ricerche automatiche periodiche |
| Config | `config.yaml` + `PyYAML` | Siti, parole chiave, preferenze per profilo |

### Ambiente di sviluppo vs produzione

| Aspetto | Sviluppo (locale Mac) | Produzione (Railway) |
|---|---|---|
| Database | SQLite | PostgreSQL (Railway managed) |
| Accesso UI | `localhost:8501` | URL pubblico Railway |
| Playwright | Locale senza config | Incluso nel container Railway |
| Deploy UI | `streamlit run app_tech.py` in terminale | Automatico ad ogni push su GitHub (web service) |
| Scheduler | LaunchAgent macOS (background silenzioso) | Railway worker service (background continuo) |

**Principio fondamentale — sviluppo e produzione identici:**
Scheduler e UI sono **due processi separati** che comunicano esclusivamente tramite il database. Questo vale sia in locale che in produzione — il codice non cambia, cambia solo come i processi vengono avviati e quale database usano.

```
Sviluppo (Mac)                    Produzione (Railway)
├── LaunchAgent                   ├── worker service
│   └── scheduler.py              │   └── scheduler.py (stesso codice)
├── terminale                     ├── web service
│   └── app_tech.py               │   └── app_tech.py (stesso codice)
└── SQLite                        └── PostgreSQL
```

SQLAlchemy astrae la differenza tra SQLite e PostgreSQL — il codice applicativo non cambia, solo la connection string nel `config.yaml`.

---

## 3. Sorgenti Dati

Le sorgenti si dividono in quattro categorie con logiche di fetching distinte:

| Categoria | Sorgenti | Come funziona |
|---|---|---|
| **Per slug** | Greenhouse, Lever | Nessun endpoint globale. Il fetcher itera su una lista di aziende definita in `config.yaml` e interroga ognuna per slug. Puro parsing JSON, nessuna autenticazione. |
| **Per keyword — API** | Adzuna, ReliefWeb, Remotive, Arbeitnow | Endpoint di ricerca globale. Una sola chiamata con keywords restituisce risultati aggregati. |
| **JobSpy** | LinkedIn, Indeed, Glassdoor, Google, ZipRecruiter | Libreria Python alto livello. Una chiamata unificata copre tutti questi siti, restituendo un dataframe Pandas già parzialmente strutturato. Nessun scraper custom da scrivere. |
| **Playwright** | Idealist, Eurobrussels, Wellfound, UN Careers | Browser automation per siti pubblici senza login ma JS-heavy, non coperti da JobSpy. Fondamentale per il profilo geopolitica. |

**Perché JobSpy e Playwright coesistono:** sono strumenti a livelli diversi. JobSpy è alto livello — per i siti che copre restituisce dati già strutturati senza scrivere nulla. Playwright è basso livello — apre un browser reale e legge il DOM dopo l'esecuzione JavaScript, necessario per siti che JobSpy non supporta. Usare Playwright per LinkedIn quando esiste JobSpy sarebbe reinventare la ruota.

### 3.1 Greenhouse (per slug)

Ogni azienda che usa Greenhouse espone un endpoint pubblico:

```
GET https://boards-api.greenhouse.io/v1/boards/{company_slug}/jobs
```

Risposta: lista di job con `id`, `title`, `location`, `updated_at`, `absolute_url`.
Per dettagli completi (descrizione, compenso, dipartimento):

```
GET https://boards-api.greenhouse.io/v1/boards/{company_slug}/jobs/{job_id}
```

**Come popolare la lista di slug:** Lista curata manualmente in `config.yaml`. Come punto di partenza esistono liste pubbliche su GitHub che raccolgono centinaia di slug di aziende note che usano Greenhouse. La lista si espande nel tempo in base alle preferenze dell'utente.

### 3.2 Lever (per slug)

Stesso modello di Greenhouse: nessun endpoint globale, ogni azienda va interrogata per slug.

```
GET https://api.lever.co/v0/postings/{company_slug}?mode=json
```

Risposta: lista di posting con `id`, `text` (titolo), `categories` (location, team, commitment), `hostedUrl`, `createdAt`.

### 3.3 Adzuna (per keyword, API gratuita)

Richiede registrazione gratuita per ottenere `app_id` e `app_key`.

```
GET https://api.adzuna.com/v1/api/jobs/{country}/search/1
    ?app_id={id}&app_key={key}&what={keywords}&where={location}
```

Aggregatore generalista utile per entrambi i profili.

### 3.4 ReliefWeb (per keyword, no autenticazione)

API completamente pubblica. Copre OCHA, UNHCR, ONG internazionali, agenzie umanitarie. Fondamentale per il profilo geopolitica.

```
GET https://api.reliefweb.int/v1/jobs
    ?appname=jobfinder&query[value]={keywords}&limit=50
```

### 3.5 Remotive (per keyword, no autenticazione)

```
GET https://remotive.com/api/remote-jobs?search={keywords}&limit=50
```

Utile per il profilo software engineer con preferenza remote.

### 3.6 Arbeitnow (per keyword, no autenticazione)

API pubblica gratuita, focalizzata su Germania ed Europa. Particolarmente rilevante per chi cerca a Berlino. Supporta filtro per visa sponsorship e remote. Zero rate limiting secondo la documentazione ufficiale.

```
GET https://www.arbeitnow.com/api/job-board-api
```

### 3.7 JobSpy — LinkedIn, Indeed, Glassdoor, Google, ZipRecruiter

`python-jobspy` è una libreria Python open source (3.4k stelle su GitHub, ultima release marzo 2025) che astrae lo scraping di cinque grandi piattaforme in un'unica interfaccia. Restituisce un dataframe Pandas con campi già normalizzati.

```python
from jobspy import scrape_jobs

jobs = scrape_jobs(
    site_name=["linkedin", "indeed", "glassdoor", "google"],
    search_term="software engineer",
    location="Berlin, Germany",
    results_wanted=50,
    hours_old=72,
    country_indeed="Germany"
)
```

Campi restituiti: `title`, `company`, `location`, `job_type`, `min_amount`, `max_amount`, `currency`, `job_url`, `description`, `emails`, `date_posted`, `is_remote`, `company_industry`.

**Limitazioni note:**
- LinkedIn blocca intorno alla decima pagina per singolo IP. Per ricerche moderate non è un problema.
- Attendere qualche secondo tra le ricerche per evitare rate limiting.
- Supporta proxies come parametro opzionale per uso futuro.

### 3.8 Playwright — Idealist, Eurobrussels, Wellfound, UN Careers

Per siti pubblici senza login che caricano i contenuti via JavaScript. Playwright apre un browser Chrome reale in modalità headless, aspetta il caricamento completo della pagina, e legge il DOM risultante. Sviluppato e mantenuto da Microsoft, scelta solida a lungo termine.

Siti target per il **profilo geopolitica:**
- **Idealist** (`idealist.org`) — no-profit, ONG, organizzazioni di impatto sociale
- **Eurobrussels** (`eurobrussels.com`) — istituzioni EU, agenzie europee, Bruxelles
- **UN Careers** (`careers.un.org`) — Nazioni Unite e agenzie affiliate

Siti target per il **profilo tech:**
- **Wellfound** (`wellfound.com`) — startup e scale-up, con salario ed equity visibili

---

## 4. Autenticazione e Gestione Utenti

L'app è multi-utente. Ogni utente ha il proprio account, i propri dati di ricerca, e le proprie preferenze. Gli utenti non vedono i dati degli altri.

`streamlit-authenticator` gestisce login e sessioni tramite un file YAML con credenziali hashate. Per la prima versione l'amministratore (tu) crea gli account manualmente. In futuro si può aggiungere una pagina di registrazione.

Ogni record nel database include un campo `user_id` che associa i dati all'utente proprietario. Le query filtrano sempre per `user_id` della sessione attiva.

---

## 5. Schema del Database

PostgreSQL in produzione, SQLite in sviluppo. Gestito con SQLAlchemy ORM.

### Tabella `users`

| Campo | Tipo | Note |
|---|---|---|
| `id` | UUID PRIMARY KEY | |
| `username` | TEXT UNIQUE | |
| `email` | TEXT | |
| `profile_type` | TEXT | `tech`, `geopolitics`, `custom` |
| `telegram_chat_id` | TEXT | Aggiunto in Fase 5 — per notifiche Telegram |
| `created_at` | DATETIME | |

### Tabella `jobs`

| Campo | Tipo | Note |
|---|---|---|
| `id` | UUID PRIMARY KEY | |
| `user_id` | UUID FK → users | Ogni annuncio appartiene a un utente |
| `source` | TEXT | `greenhouse`, `lever`, `linkedin`, `indeed`, `idealist`, ecc. |
| `source_id` | TEXT | ID originale nella sorgente |
| `company` | TEXT | Nome azienda |
| `company_slug` | TEXT | Slug (solo per Greenhouse/Lever) |
| `title` | TEXT | Titolo della posizione |
| `industry` | TEXT | Settore (tech, ngo, finance...) |
| `location` | TEXT | Luogo (città, paese, "Remote") |
| `remote` | BOOLEAN | True se remote/hybrid |
| `salary_min` | INTEGER | Stipendio minimo (se disponibile) |
| `salary_max` | INTEGER | Stipendio massimo (se disponibile) |
| `salary_currency` | TEXT | EUR, USD, ecc. |
| `contract_type` | TEXT | Full-time, Part-time, Contract... |
| `url` | TEXT | Link all'annuncio originale |
| `email` | TEXT | Contatto email (se presente) |
| `phone` | TEXT | Contatto telefono (se presente) |
| `description` | TEXT | Testo completo dell'annuncio |
| `raw_data` | TEXT | JSON grezzo originale |
| `tags` | TEXT | JSON array di tag/keywords |
| `posted_at` | DATETIME | Data pubblicazione annuncio |
| `fetched_at` | DATETIME | Data fetch |
| `application_sent` | BOOLEAN | Default False |
| `application_date` | DATE | Data invio candidatura |
| `notes` | TEXT | Note personali |
| `status` | TEXT | `new`, `saved`, `applied`, `rejected`, `interview` |

### Tabella `sources`

| Campo | Tipo | Note |
|---|---|---|
| `id` | UUID PRIMARY KEY | |
| `user_id` | UUID FK → users | |
| `name` | TEXT | Nome sorgente |
| `type` | TEXT | `slug`, `api`, `jobspy`, `playwright` |
| `slug_or_url` | TEXT | Parametro per la chiamata |
| `active` | BOOLEAN | Abilitata o no |

### Tabella `searches`

| Campo | Tipo | Note |
|---|---|---|
| `id` | UUID PRIMARY KEY | |
| `user_id` | UUID FK → users | |
| `keywords` | TEXT | Parole chiave usate |
| `sources` | TEXT | JSON array sorgenti usate |
| `results_count` | INTEGER | Annunci trovati |
| `searched_at` | DATETIME | Timestamp |

### Tabella `profiles`

| Campo | Tipo | Note |
|---|---|---|
| `id` | UUID PRIMARY KEY | |
| `user_id` | UUID FK → users | |
| `name` | TEXT | Es. "Software Engineer", "Geopolitics" |
| `keywords_default` | TEXT | JSON array keywords predefinite |
| `locations_filter` | TEXT | JSON array luoghi preferiti |
| `remote_only` | BOOLEAN | |
| `salary_min` | INTEGER | Filtro stipendio minimo |
| `salary_max` | INTEGER | Filtro stipendio massimo |

---

## 6. Architettura dei Moduli

```
job_finder/
├── app.py                      ← Entry point Streamlit
├── config.yaml                 ← API keys, credenziali utenti (hashate), DB connection
├── requirements.txt
├── Dockerfile                  ← Per Railway (include Playwright + Chromium)
│
├── db/
│   ├── models.py               ← Definizione tabelle SQLAlchemy
│   ├── database.py             ← Connessione, sessione, init (SQLite/PostgreSQL)
│   └── queries.py              ← Query comuni filtrate per user_id
│
├── fetchers/
│   ├── base.py                 ← Classe astratta BaseFetcher
│   ├── slug_fetcher.py         ← Classe base per sorgenti per-slug
│   ├── keyword_fetcher.py      ← Classe base per sorgenti per-keyword
│   ├── greenhouse.py           ← Itera su lista slug → GET /boards/{slug}/jobs
│   ├── lever.py                ← Itera su lista slug → GET /postings/{slug}
│   ├── adzuna.py               ← GET /jobs/search?what={kw}
│   ├── reliefweb.py            ← GET /v1/jobs?query={kw}
│   ├── remotive.py             ← GET /api/remote-jobs?search={kw}
│   ├── arbeitnow.py            ← GET /api/job-board-api
│   ├── jobspy_adapter.py       ← Wrapper JobSpy → LinkedIn, Indeed, Glassdoor, Google
│   └── playwright_fetcher.py   ← Browser automation → Idealist, Eurobrussels, Wellfound, UN Careers
│
├── core/
│   ├── normalizer.py           ← Tutti i formati → schema canonico
│   ├── deduplicator.py         ← Evita duplicati per user_id
│   ├── filters.py              ← Logica di filtraggio
│   └── search_engine.py        ← Orchestratore: fetcher → normalizza → salva
│
└── ui/
    ├── pages/
    │   ├── login.py            ← Pagina login (streamlit-authenticator)
    │   ├── search.py           ← Pagina ricerca
    │   ├── dashboard.py        ← Dashboard annunci
    │   └── settings.py         ← Profilo utente, sorgenti, preferenze
    └── components/
        ├── job_table.py        ← Tabella annunci interattiva
        └── filters_panel.py    ← Pannello filtri laterale
```

---

## 7. Flusso Dati End-to-End

```
[Utente fa login → inserisce keywords → seleziona sorgenti]
            │
            ▼
    search_engine.py (con user_id della sessione)
            │
            ├── [per slug] ──────────────────────────────────────────┐
            │   ├──► greenhouse.py → for slug in list: GET /boards/  │
            │   └──► lever.py      → for slug in list: GET /postings/│
            │                                                         │
            ├── [per keyword — API] ─────────────────────────────────┤
            │   ├──► reliefweb.py  → GET /v1/jobs?query={kw}         │
            │   ├──► adzuna.py     → GET /jobs/search?what={kw}      │
            │   ├──► remotive.py   → GET /remote-jobs?search={kw}    │
            │   └──► arbeitnow.py  → GET /api/job-board-api          │
            │                                                         │
            ├── [JobSpy] ───────────────────────────────────────────►├──► normalizer.py
            │   └──► jobspy_adapter.py                               │   (tutto → schema canonico)
            │           └──► scrape_jobs(linkedin, indeed,           │        + user_id
            │                           glassdoor, google)           │
            │                                                         │
            └── [Playwright] ────────────────────────────────────────┘
                └──► playwright_fetcher.py
                        ├──► idealist.org
                        ├──► eurobrussels.com
                        ├──► wellfound.com
                        └──► careers.un.org
                                        │
                                        ▼
                                deduplicator.py
                                (controlla duplicati per user_id)
                                        │
                                        ▼
                                  PostgreSQL (Railway)
                                        │
                                        ▼
                          [Dashboard: tabella filtrabile per utente]
                          [Utente marca "Application Sent"]
```

---

## 8. Interfaccia Utente (Streamlit)

### Stile visivo

- **Tema:** dark mode
- **Sfondo:** `#0F1117` (default Streamlit dark)
- **Superficie sezioni/cards:** `#1E2130`
- **Accento primario:** `#00FF94` (verde elettrico)
- **Accento secondario:** `#4F8EF7` (blu — link e azioni secondarie)
- **Testo principale:** `#FFFFFF`
- **Testo secondario:** `#8B9BB4`
- **Stato interessante:** `#00C853` (verde) 🟢
- **Stato non interessante:** `#FF3B3B` (rosso) 🔴
- **Stato nuovo:** `#4A4A5A` (grigio) ⚫

### Navigazione — schede in alto

```
[  📋 Risultati  ]  [  🔍 Ricerca  ]  [  ⚙️ Account  ]
```

La scheda **Risultati** è quella primaria — è la prima che l'utente vede dopo il login. Le altre due si toccano raramente.

---

### Scheda 0 — Login

Form di login con username e password. Sessione persistente per la durata della visita. Gestito da `streamlit-authenticator`.

---

### Scheda 1 — Risultati (primaria)

La scheda è divisa in tre sezioni verticali che scorrono dall'alto verso il basso.

**Header con statistiche:**
```
✨ 12 nuovi oggi    📁 47 totali    ✅ 8 candidature inviate
```

**Sezione A — Nuovi oggi**

Lista degli annunci trovati nell'ultima ricerca automatica. Sfondo leggermente distinto per evidenziarla. Se non ci sono nuovi annunci la sezione è nascosta.

Nessun filtro in questa sezione — sono pochi annunci, si scorrono tutti.

```
┌─ NUOVI OGGI ──────────────────────────────────────────┐
│ ⚫  Adobe      Sr. Engineer    Basel      60-80k €    │
│ ⚫  Spotify    DevOps          Remote     70-90k €    │
│ ⚫  Zalando    Fullstack       Berlin     65-85k €    │
│  [click su riga → espande dettaglio inline]           │
└───────────────────────────────────────────────────────┘
```

**Sezione B — 🟢 Interessanti**

Tutti gli annunci marcati come interessanti. Filtro candidatura in cima alla sezione.

```
┌─ 🟢 INTERESSANTI ─────────────────────────────────────┐
│  [Tutti]  [✅ Candidatura inviata]  [📭 Non inviata]  │
│                                                       │
│ 🟢  Adobe      Internship      Basel      n/d         │
│ 🟢  Novartis   Data Engineer   Basel      80-100k €   │
└───────────────────────────────────────────────────────┘
```

**Sezione C — 🔴 Non interessanti**

Annunci archiviati, visibili ma in secondo piano. Nessun filtro.

```
┌─ 🔴 NON INTERESSANTI ─────────────────────────────────┐
│ 🔴  Roche      Backend Dev     Zurigo     n/d         │
│ 🔴  Hitachi    Cloud Arch.     Londra     90-110k €   │
└───────────────────────────────────────────────────────┘
```

**Colonne della tabella** (identiche in tutte e tre le sezioni):
stato (pallino colorato), Azienda, Posizione, Luogo, Stipendio, Sorgente, Data pubblicazione, Link, Email

**Dettaglio espandibile al click su riga:**

Appare inline sotto la riga selezionata, senza cambiare pagina. Disponibile in tutte e tre le sezioni.

```
┌─ DETTAGLIO: Adobe — Senior Engineer ──────────────────┐
│ 📍 Basel   💰 60-80k EUR   📅 pubblicato oggi          │
│ 🔗 careers.adobe.com   📧 jobs@adobe.com              │
│ Industry: Media / Software                            │
│                                                       │
│ Stato attuale: ⚫ Nuovo                               │
│ [🟢 Interessante]              [🔴 Non interessante]  │
│                                                       │
│ ☐ Candidatura inviata   📅 [__/__/____]               │
│    (il campo data appare solo se checkbox spuntata)   │
│                                                       │
│ Note: ____________________________________________    │
└───────────────────────────────────────────────────────┘
```

Lo stato è sempre modificabile — un annuncio non interessante può essere riportato a interessante in qualsiasi momento cliccando il bottone corrispondente. Il cambio di stato sposta l'annuncio immediatamente nella sezione corretta.

---

### Scheda 2 — Ricerca

Divisa in due blocchi: parametri di ricerca automatica e aziende monitorate manualmente.

**Blocco A — Parametri di ricerca**

```
┌─ PARAMETRI ───────────────────────────────────────────┐
│                                                       │
│  Keywords                                             │
│  ┌───────────────────────────────────────────────┐   │
│  │ software engineer, python, backend, remote    │   │
│  └───────────────────────────────────────────────┘   │
│  (separate da virgola — trova annunci con             │
│   almeno una keyword)                                 │
│                                                       │
│  Location                        Remote              │
│  ┌─────────────────────────┐     ☑ Includi remote    │
│  │ Berlin, Germany         │                         │
│  └─────────────────────────┘                         │
│                                                       │
│  Sorgenti attive                                      │
│  ☑ LinkedIn    ☑ Indeed     ☑ Glassdoor              │
│  ☑ Greenhouse  ☑ Lever      ☑ Arbeitnow              │
│  ☑ Remotive    ☐ ReliefWeb  ☐ Adzuna                 │
│                                                       │
│  Ricerca automatica                                   │
│  ☑ Ogni giorno alle [08:00 ▼]                        │
│  Prossima ricerca: domani alle 08:00                  │
│                                                       │
│  [💾 SALVA]                    [▶ CERCA ORA]         │
└───────────────────────────────────────────────────────┘
```

- **Salva** — aggiorna le preferenze senza avviare ricerca
- **Cerca ora** — salva e avvia immediatamente una ricerca, poi riporta alla scheda Risultati

**Blocco B — Aziende monitorate**

Aziende controllate ogni giorno da Playwright indipendentemente dalle keywords. Corrisponde alla colonna "aziende monitorate manualmente" dello screenshot originale.

```
┌─ AZIENDE MONITORATE ──────────────────────────────────┐
│                                                       │
│  AZIENDA      URL CAREERS             ULTIMO CHECK    │
│  Adobe        adobe.com/careers       oggi  ✓   🗑   │
│  Spotify      spotify.com/jobs        oggi  ✓   🗑   │
│  Zalando      zalando.jobs            ieri  ✓   🗑   │
│  Roche        roche.com/careers       oggi  ✗   🗑   │
│                                                       │
│  ✓ = pagina raggiunta correttamente                   │
│  ✗ = problema (URL non raggiungibile o pagina cambiata)│
│                                                       │
│  [+ Aggiungi azienda]                                 │
└───────────────────────────────────────────────────────┘
```

---

### Scheda 3 — Account

Minimale. Contiene: nome utente, email, cambio password, orario notifica Telegram (Fase 5), e bottone per cancellare tutti i propri dati.

---

## 9. Normalizzazione — Mapping dei Campi

| Campo canonico | Greenhouse | Lever | ReliefWeb | JobSpy |
|---|---|---|---|---|
| `title` | `title` | `text` | `fields.title` | `title` |
| `company` | da slug | da slug | `fields.source[0].name` | `company` |
| `location` | `location.name` | `categories.location` | `fields.city[0]` | `location.city` |
| `url` | `absolute_url` | `hostedUrl` | `fields.url[0].url` | `job_url` |
| `posted_at` | `updated_at` | `createdAt` (epoch ms) | `fields.date.created` | `date_posted` |
| `salary_min` | raramente disponibile | raramente disponibile | raramente disponibile | `min_amount` |
| `salary_max` | raramente disponibile | raramente disponibile | raramente disponibile | `max_amount` |
| `email` | raramente disponibile | raramente disponibile | raramente disponibile | `emails[0]` |
| `remote` | da testo location | da `commitment` | raramente disponibile | `is_remote` |

I campi mancanti vengono impostati a `None`. Il campo `user_id` viene aggiunto dal normalizzatore dalla sessione attiva.

---

## 10. Deduplicazione

Un annuncio è duplicato se esiste già nel DB con la stessa coppia `(user_id, source, source_id)`. Per annunci provenienti da sorgenti diverse ma potenzialmente identici (es. stesso annuncio su Indeed via JobSpy e su Adzuna), verifica fuzzy su `(user_id, company, title, location)` con soglia di similarità.

---

## 11. Hosting — Railway

Railway è una piattaforma cloud che deploya automaticamente l'app ad ogni push su GitHub. Include PostgreSQL come servizio nativo (un click per aggiungere il database). Supporta Playwright tramite Dockerfile con Chromium incluso.

**Costi:** 5 dollari di credito gratuito al mese. Per un progetto piccolo può bastare; altrimenti il costo è proporzionale all'utilizzo.

**Flusso di deploy:**
1. Push del codice su GitHub
2. Railway rileva il cambiamento e avvia il build automatico
3. L'app è disponibile sull'URL pubblico Railway in pochi minuti

**Variabili d'ambiente su Railway** (non nel codice):
- `DATABASE_URL` — connection string PostgreSQL
- `ADZUNA_APP_ID` e `ADZUNA_APP_KEY`
- `SECRET_KEY` — per streamlit-authenticator

---

## 12. Roadmap di Sviluppo

### Fase 1 — MVP locale
- [ ] Setup database SQLAlchemy (SQLite in sviluppo)
- [ ] Fetcher Greenhouse + Lever
- [ ] Integrazione JobSpy (LinkedIn, Indeed, Glassdoor, Google)
- [ ] Normalizzatore base
- [ ] UI: login + ricerca + dashboard tabella minimale
- [ ] Campo "Application Sent" con checkbox e data

### Fase 2 — Espansione sorgenti API
- [ ] Fetcher ReliefWeb
- [ ] Fetcher Arbeitnow
- [ ] Fetcher Remotive
- [ ] Fetcher Adzuna
- [ ] Deduplicazione cross-sorgente

### Fase 3 — Playwright (profilo geopolitica completo)
- [ ] Setup Playwright
- [ ] Scraper Idealist
- [ ] Scraper Eurobrussels
- [ ] Scraper UN Careers
- [ ] Scraper Wellfound

### Fase 4 — Deploy Railway
- [ ] Migrazione da SQLite a PostgreSQL
- [ ] Dockerfile con Playwright + Chromium
- [ ] Configurazione variabili d'ambiente Railway
- [ ] Deploy e test su URL pubblico

### Fase 5 — UX e funzionalità avanzate
- [ ] Export CSV
- [ ] Pagina registrazione utenti
- [ ] Bot Telegram per notifiche push (`python-telegram-bot`)
  - Creazione bot via @BotFather (token API gratuito)
  - Campo `telegram_chat_id` aggiunto alla tabella `users`
  - Notifica nuovi annunci corrispondenti alle keywords dell'utente
  - Riepilogo giornaliero opzionale
  - Reminder candidature senza risposta
  - Architettura bidirezionale: in futuro possibile mandare comandi da Telegram (es. `/cerca software engineer berlino`)

---

## 14. Struttura del `config.yaml`

Il file `config.yaml` è l'unica fonte di verità per tutta la configurazione. Viene letto all'avvio sia da `scheduler.py` che da `app_tech.py`. Le informazioni sensibili (API keys, password) in produzione vengono sovrascritte dalle variabili d'ambiente Railway.

```yaml
# ─── DATABASE ─────────────────────────────────────────────────────
database:
  url: "sqlite:///jobfinder.db"          # sviluppo locale
  # url: "postgresql://..."              # produzione — sovrascritta da Railway env var

# ─── AUTENTICAZIONE ───────────────────────────────────────────────
auth:
  secret_key: "dev-secret-key"           # produzione — sovrascritta da Railway env var
  cookie_expiry_days: 7

# ─── PROFILI UTENTE ───────────────────────────────────────────────
profiles:
  tech:
    name: "Software Engineer"
    keywords_default:
      - "software engineer"
      - "backend developer"
      - "python developer"
    location_default: "Berlin, Germany"
    remote: true
    sources_default:
      - linkedin
      - indeed
      - glassdoor
      - greenhouse
      - lever
      - remotive
      - arbeitnow

  geopolitics:
    name: "Geopolitica / Relazioni Internazionali"
    keywords_default:
      - "policy analyst"
      - "international relations"
      - "foreign affairs"
    location_default: ""
    remote: true
    sources_default:
      - reliefweb
      - idealist
      - eurobrussels
      - un_careers
      - linkedin
      - indeed

# ─── SORGENTI PER SLUG (Greenhouse / Lever) ───────────────────────
slug_sources:
  greenhouse:
    - spotify
    - stripe
    - zalando
    - adobe
    - n26
    - delivery-hero

  lever:
    - soundcloud
    - sumup
    - gorillas

# ─── API KEYS ─────────────────────────────────────────────────────
api_keys:
  adzuna_app_id: ""                      # produzione — sovrascritta da Railway env var
  adzuna_app_key: ""                     # produzione — sovrascritta da Railway env var

# ─── SCHEDULER ────────────────────────────────────────────────────
scheduler:
  default_time: "08:00"                  # orario ricerca automatica di default
  timezone: "Europe/Berlin"

# ─── LOGGING ──────────────────────────────────────────────────────
logging:
  level: "INFO"                          # DEBUG in sviluppo, INFO in produzione
  file: "jobfinder.log"
```

**Variabili d'ambiente Railway** (sovrascrivono il config.yaml in produzione):
- `DATABASE_URL` — connection string PostgreSQL
- `ADZUNA_APP_ID`, `ADZUNA_APP_KEY`
- `SECRET_KEY` — per streamlit-authenticator
- `TELEGRAM_BOT_TOKEN` — Fase 5

---

## 15. Contratti tra Moduli

Definisce esattamente cosa ogni modulo riceve e restituisce. Tutti i fetcher rispettano la stessa interfaccia — il normalizzatore non sa da quale fetcher arrivano i dati, li tratta tutti allo stesso modo.

### Output standard di ogni fetcher

Ogni fetcher restituisce una **lista di dizionari** con queste chiavi garantite:

```python
{
    "source": str,          # "greenhouse", "lever", "linkedin", "reliefweb", ecc.
    "source_id": str,       # ID originale nella sorgente (stringa, anche se numerico)
    "raw_data": dict,       # JSON grezzo originale, non modificato
    # tutti gli altri campi possono essere None se non disponibili
    "title": str | None,
    "company": str | None,
    "location": str | None,
    "remote": bool | None,
    "salary_min": int | None,
    "salary_max": int | None,
    "salary_currency": str | None,
    "contract_type": str | None,
    "url": str | None,
    "email": str | None,
    "phone": str | None,
    "description": str | None,
    "industry": str | None,
    "tags": list[str],      # lista vuota se non disponibile, mai None
    "posted_at": str | None,  # ISO 8601: "2026-05-20T10:30:00"
}
```

### Input/Output del normalizzatore

**Input:** dizionario con la struttura sopra (output del fetcher)
**Output:** dizionario pronto per il database, con `user_id` aggiunto e `fetched_at` impostato al timestamp corrente. I campi `None` rimangono `None` — il normalizzatore non inventa dati.

### Input/Output del deduplicatore

**Input:** dizionario normalizzato + sessione database
**Output:** `True` se l'annuncio è nuovo e va salvato, `False` se è già presente nel DB per quell'utente (stesso `source` + `source_id`)

### Output dello search engine verso la UI

Lo search engine restituisce un dizionario di riepilogo:

```python
{
    "total_found": int,
    "new_jobs": int,
    "errors": [
        {
            "source": str,      # nome della sorgente
            "error": str,       # messaggio di errore leggibile
            "recoverable": bool # True = riprovare, False = configurazione errata
        }
    ]
}
```

---

## 16. Gestione Errori e Logging

### Principio generale

Se una sorgente fallisce, viene saltata e la ricerca continua con le altre. L'utente vede nella UI quali sorgenti hanno avuto problemi, con un messaggio leggibile. Il programma non crasha mai per un errore di singola sorgente.

### Tipi di errore e comportamento

| Tipo di errore | Esempio | Comportamento |
|---|---|---|
| Sorgente irraggiungibile | timeout di rete | Salta la sorgente, logga, mostra warning in UI |
| Rate limiting (429) | LinkedIn blocca | Salta la sorgente, logga con timestamp, mostra warning in UI |
| Parsing fallito | HTML cambiato | Salta la sorgente, logga con dettaglio, mostra warning in UI |
| API key mancante | Adzuna senza chiave | Mostra errore configurazione in UI, non ritenta |
| Database irraggiungibile | SQLite corrotto | Blocca tutto, mostra errore critico, non continua |
| Playwright timeout | Pagina non carica | Salta l'azienda monitorata, aggiorna stato con ✗ in UI |

### Visualizzazione errori in UI

Nella scheda Risultati, dopo una ricerca, appare una sezione collassabile:

```
⚠️ 2 sorgenti hanno avuto problemi — clicca per dettagli

  🔴 LinkedIn — rate limiting raggiunto. Riprova tra qualche ora.
  🔴 Eurobrussels — pagina non raggiungibile (timeout). Controlla l'URL.
```

Gli errori di configurazione (API key mancante) appaiono invece nella scheda Ricerca, vicino alla sorgente coinvolta.

### Logging

Ogni operazione significativa viene loggata in `jobfinder.log`:

```
2026-05-20 08:00:01 INFO  Scheduler: avvio ricerca automatica per utente mario
2026-05-20 08:00:03 INFO  Greenhouse: trovati 12 annunci (spotify: 3, zalando: 5, adobe: 4)
2026-05-20 08:00:07 WARNING LinkedIn: rate limiting (429) — sorgente saltata
2026-05-20 08:00:09 INFO  ReliefWeb: trovati 8 annunci
2026-05-20 08:00:11 INFO  Deduplicatore: 6 nuovi annunci, 14 già presenti
2026-05-20 08:00:11 INFO  Database: 6 annunci salvati per utente mario
2026-05-20 08:00:11 INFO  Ricerca completata: 6 nuovi su 20 trovati
```

In sviluppo il livello di log è `DEBUG` (mostra tutto). In produzione è `INFO` (solo operazioni significative ed errori).

---


## 17. Dipendenze Python

```
streamlit
streamlit-authenticator
httpx
sqlalchemy
psycopg2-binary
pyyaml
apscheduler
python-jobspy
playwright
```

---
## 18. Utilizzo in development
```
Comandi
Start Streamlit + program: python3 -m streamlit run job_finder/app.py
Test Suite (local): PYTHONPATH=. pytest

flush command (flushes search result and search results+search history)
all users:
JOBFINDER_ENV=dev python3 -m job_finder.dev_tools flush-search-results --yes
only one user:
JOBFINDER_ENV=dev python3 -m job_finder.dev_tools flush-search-results --user admin --yes
delete search history:
JOBFINDER_ENV=dev python3 -m job_finder.dev_tools flush-search-results --include-searches --yes
```

*Documento di riferimento — aggiornare prima di ogni sessione di sviluppo.*
