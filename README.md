# Dall'argilla al cloud

**Progettazione di una piattaforma web per la digitalizzazione di una bottega di ceramica**

Project Work di Laurea Triennale in Informatica per le aziende digitali (L-31), Università Telematica Pegaso.
Autore: Emanuele Francesco Cannella. Tema 1, *La digitalizzazione dell'impresa*, traccia n. 22.

## Il progetto

*Bottega Terracotta Viva* è un laboratorio di ceramica di fantasia che oggi gestisce corsi, prenotazioni e
iscritti con strumenti frammentati: agenda cartacea, messaggi e fogli di calcolo. Questa piattaforma ne
digitalizza i processi principali con l'obiettivo di avvicinare i giovani all'arte ceramica:

- **vetrina pubblica**: storia e filosofia della bottega, catalogo di corsi, esperienze e pacchetti;
- **area personale del cliente**: registrazione, profilo, prenotazioni, corsi, pagamenti simulati;
- **pannello di amministrazione**: gestione dell'offerta, del calendario e dashboard con gli indicatori.

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

## Avvio del progetto

> Le istruzioni saranno completate man mano che il prototipo prende forma.

## Stato dei lavori

- [x] Struttura del repository
- [ ] Analisi dei requisiti e casi d'uso
- [ ] Progettazione: architettura, modello ER, API
- [ ] Back-end e database
- [ ] Front-end
- [ ] Test funzionali e documentazione
