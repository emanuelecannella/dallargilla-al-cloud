# Dall'argilla al cloud

**Progettazione di una piattaforma web per la digitalizzazione di una bottega di ceramica**

Project Work di Laurea Triennale in Informatica per le aziende digitali (L-31), Università Telematica Pegaso.
Autore: Emanuele Francesco Cannella. Tema 1, *La digitalizzazione dell'impresa*, traccia n. 22.

## Il progetto

Bottega Terracotta Viva è un laboratorio di ceramica immaginario, nel centro storico di Palermo, che oggi gestisce corsi e prenotazioni con agenda cartacea, messaggi e fogli di calcolo. L’idea del progetto è nata dal desiderio di far avvicinare i giovani, attraverso un semplice smartphone, a una realtà artigianale sempre più rara, un’arte preziosa che potrebbe diventare non solo un ritrovo culturale, spazio di crescita e condivisione, ma anche una risorsa per la città, dal punto di vista culturale ed economico. La piattaforma aiuta il cliente ad avvicinarsi a questa realtà attraverso una vetrina digitale che raccoglie tutte le informazioni utili, dotata di un’area personale in cui gestire prenotazioni, pagamenti, promemoria e ricevute. Allo stesso tempo, semplifica anche il lavoro della titolare, che può creare e gestire corsi ed esperienze, seguire le prenotazioni e monitorare i posti disponibili e i pagamenti dei clienti, avendo un quadro chiaro e generale della propria attività.

## Architettura

| Livello | Tecnologia |
| --- | --- |
| Front-end | React + Vite |
| Back-end e API | Python 3, FastAPI (API REST, documentazione OpenAPI) |
| Database | PostgreSQL, SQLAlchemy, migrazioni Alembic |
| Sicurezza | Hash delle password con bcrypt, autenticazione JWT, ruoli cliente e amministratore |
| Infrastruttura | Docker Compose |

## Struttura del repository

```
backend/    API, logica di business, modelli dei dati e test
frontend/   interfaccia web React
docs/       diagrammi UML ed ER, documentazione delle API, screenshot dei test
```

## Documentazione

| Documento | Contenuto |
| --- | --- |
| [Requisiti](docs/requisiti.md) | Processo attuale della bottega, attori, requisiti e regole di business |
| [Casi d'uso](docs/diagrammi/casi-d-uso.md) | Diagramma e specifica dei casi d'uso principali |
| [Stati della prenotazione](docs/diagrammi/stati-prenotazione.md) | Diagramma di macchina a stati: in attesa, confermata, annullata |
| [Architettura](docs/architettura.md) | Livelli del sistema, flusso di una prenotazione, sicurezza |
| [Modello dei dati](docs/modello-dati.md) | Diagramma ER, scelte di modellazione, vincoli di integrità |
| [API](docs/api.md) | Endpoint, convenzioni, codici di risposta ed esempi |
| [Scenari di test](docs/scenari-di-test.md) | Test funzionali dal punto di vista di chi usa il sito, con screenshot |

## Avvio del progetto

Serve soltanto [Docker Desktop](https://www.docker.com/products/docker-desktop/) installato e avviato.

1. Copia il file `.env.example` in un nuovo file chiamato `.env` (e, se vuoi, cambia password e chiave segreta).
2. Dalla cartella del progetto avvia tutto con:

   ```bash
   docker compose up --build
   ```

3. Al primo avvio Docker scarica le immagini e crea le tabelle del database (servono alcuni minuti).
   In un secondo terminale carica i dati iniziali della bottega (listino, calendario, amministratore):

   ```bash
   docker compose run --rm backend python -m app.seed
   ```

4. Apri nel browser:
   - <http://localhost:5173>: il sito di Bottega Terracotta Viva
   - <http://localhost:8000/api/v1/salute>: deve rispondere `{"stato": "ok", ...}`
   - <http://localhost:8000/docs>: documentazione interattiva delle API (Swagger)

Per provare le API protette: in `/docs` usa `POST /auth/registrazione`, poi `POST /auth/login`, copia l'`access_token` e incollalo nel pulsante **Authorize**.

### Dati dimostrativi (facoltativi)

Per vedere il sito come una bottega già avviata, con clienti, prenotazioni, pagamenti, recensioni e una dashboard con dei numeri, dopo i dati iniziali esegui:

```bash
docker compose run --rm backend python -m app.demo
```

Lo script crea cinque clienti di fantasia (password per tutti: `Bottega2026`):

| Cliente | Email | Cosa si vede accedendo |
| --- | --- | --- |
| Giulia Rossi (meno di 26 anni) | giulia@demo.terracotta-viva.example | sconto Under 26 applicato da solo, una recensione, un'esperienza in arrivo |
| Marco Bianchi | marco@demo.terracotta-viva.example | pacchetto "Giornata in bottega" con un'esperienza ancora da prenotare |
| Sara Esposito | sara@demo.terracotta-viva.example | membership di coworking con gli ingressi rimasti |
| Luca Ferraro | luca@demo.terracotta-viva.example | pagamento rifiutato: la prenotazione resta in attesa |
| Anna Greco | anna@demo.terracotta-viva.example | corso di tornio con il codice promozionale `AUTUNNO15` |

Tutti i dati sono inventati, telefoni compresi. Lo script si può rilanciare: se i clienti esistono già non duplica nulla.

Per fermare tutto: `Ctrl+C`, oppure `docker compose down`.

### Eseguire i test

```bash
docker compose run --rm backend pytest -v      # test del back-end
docker compose run --rm frontend npm test      # test del front-end
```

### Ripartire da un database vuoto

Per cancellare tutti i dati e ricaricare quelli iniziali (utile dopo un aggiornamento dei dati della bottega):

```bash
docker compose down -v
docker compose up --build
docker compose run --rm backend python -m app.seed
docker compose run --rm backend python -m app.demo   # facoltativo
```

## Stato dei lavori

- [x] Struttura del repository
- [x] Analisi dei requisiti e casi d'uso ([requisiti](docs/requisiti.md), [casi d'uso](docs/diagrammi/casi-d-uso.md))
- [x] Progettazione: [architettura](docs/architettura.md), [modello dei dati](docs/modello-dati.md), [API](docs/api.md), [stati della prenotazione](docs/diagrammi/stati-prenotazione.md)
- [x] Back-end e database: tutte le 30 operazioni della [specifica API](docs/api.md), 71 test automatici
- [x] Front-end: vetrina con le foto dei pezzi, catalogo e calendario, registrazione, area personale con prenotazioni, pagamenti simulati, ricevute e promemoria, pacchetti e membership, recensioni, pannello della titolare con dashboard, iscritti e gestione dell'offerta; 21 test automatici
- [x] Dati dimostrativi con clienti di prova
- [x] [Scenari di test funzionale](docs/scenari-di-test.md) con screenshot, anche da smartphone
