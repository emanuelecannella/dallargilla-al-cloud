# Specifica delle API

Le API seguono lo stile **REST**: ogni risorsa (servizi, sessioni, prenotazioni…) ha un indirizzo, e il
metodo HTTP indica l'operazione. Tutti gli indirizzi iniziano con `/api/v1`: il numero di versione permette
di evolvere le API in futuro senza rompere i client esistenti.

Questa specifica è il "contratto" tra front-end e back-end, scritto prima del codice. A prototipo avviato,
la documentazione interattiva generata da FastAPI (OpenAPI/Swagger) è disponibile su `/docs`.

## Convenzioni

| Aspetto | Regola |
| --- | --- |
| Formato | Richieste e risposte in JSON, codifica UTF-8 |
| Autenticazione | Intestazione `Authorization: Bearer <token>` sugli endpoint protetti |
| Importi | Interi in centesimi di euro (`8500` = 85,00 €) |
| Date e orari | Formato ISO 8601 (`2026-11-07T10:00:00+01:00`) |
| Paginazione | Parametri `pagina` e `per_pagina` sugli elenchi lunghi |

## Codici di risposta

| Codice | Significato | Esempio |
| --- | --- | --- |
| `200 OK` | Richiesta riuscita | Lettura del catalogo |
| `201 Created` | Risorsa creata | Nuova prenotazione |
| `204 No Content` | Riuscita, nessun contenuto da restituire | Annullamento |
| `400 Bad Request` | Richiesta non ammessa dalle regole | Cancellazione oltre le 48 ore (RB05) |
| `401 Unauthorized` | Token mancante o scaduto | Accesso all'area personale senza login |
| `403 Forbidden` | Ruolo non sufficiente | Cliente che apre la dashboard admin |
| `404 Not Found` | Risorsa inesistente | Corso con slug sbagliato |
| `409 Conflict` | Conflitto con lo stato attuale | Posti esauriti (RB01) o doppia prenotazione (RB02) |
| `422 Unprocessable Entity` | Dati non validi | Email in formato errato |

Gli errori hanno sempre la stessa forma, così il front-end li mostra in modo uniforme:

```json
{ "detail": "Posti esauriti per questa sessione", "codice": "POSTI_ESAURITI" }
```

## Endpoint

Legenda accesso: **P** pubblico, **C** cliente autenticato, **A** amministratore.

### Autenticazione e profilo

| Metodo | Percorso | Accesso | Descrizione | Requisito |
| --- | --- | --- | --- | --- |
| POST | `/auth/registrazione` | P | Crea un account cliente | RF05 |
| POST | `/auth/login` | P | Restituisce il token JWT | RF06 |
| GET | `/utenti/me` | C | Dati del profilo | RF07 |
| PATCH | `/utenti/me` | C | Modifica del profilo | RF07 |

### Catalogo

| Metodo | Percorso | Accesso | Descrizione | Requisito |
| --- | --- | --- | --- | --- |
| GET | `/servizi?tipo=corso` | P | Elenco dei servizi attivi, filtrabile per tipo | RF02, RF03 |
| GET | `/servizi/{slug}` | P | Dettaglio di un servizio | RF02 |
| GET | `/servizi/{id}/sessioni` | P | Date future con posti residui | RF04 |
| GET | `/servizi/{id}/valutazioni` | P | Recensioni e voto medio | RF13 |
| GET | `/pacchetti` | P | Pacchetti di esperienze | RF02 |
| GET | `/piani-membership` | P | Piani di coworking | RF02 |

### Prenotazioni, acquisti e pagamenti

| Metodo | Percorso | Accesso | Descrizione | Requisito |
| --- | --- | --- | --- | --- |
| POST | `/prenotazioni` | C | Prenota una sessione, con codice promo facoltativo | RF08, RF14 |
| GET | `/prenotazioni/mie` | C | Prenotazioni future e passate | RF11 |
| DELETE | `/prenotazioni/{id}` | C | Annulla una prenotazione | RF12, RB05 |
| POST | `/prenotazioni/{id}/pagamento` | C | Paga una prenotazione (simulato) | RF10 |
| POST | `/acquisti` | C | Acquista un pacchetto o una membership | RF09 |
| GET | `/acquisti/miei` | C | Pacchetti e membership, con ingressi residui | RF09 |
| POST | `/acquisti/{id}/pagamento` | C | Paga un acquisto (simulato) | RF10 |
| GET | `/pagamenti/{codice}/ricevuta` | C | Ricevuta di un pagamento | RF10 |
| POST | `/valutazioni` | C | Valuta un'attività svolta | RF13, RB07 |

### Amministrazione

| Metodo | Percorso | Accesso | Descrizione | Requisito |
| --- | --- | --- | --- | --- |
| GET, POST | `/admin/servizi` | A | Elenco e creazione dei servizi | RF15 |
| PATCH, DELETE | `/admin/servizi/{id}` | A | Modifica o disattivazione | RF15 |
| POST | `/admin/sessioni` | A | Pubblica una nuova data | RF16 |
| PATCH | `/admin/sessioni/{id}` | A | Modifica o annulla una data | RF16 |
| GET | `/admin/sessioni/{id}/iscritti` | A | Elenco iscritti di una data | RF17 |
| GET, POST | `/admin/promozioni` | A | Elenco e creazione delle promozioni | RF18 |
| PATCH | `/admin/promozioni/{id}` | A | Modifica o disattiva una promozione | RF18 |
| GET | `/admin/dashboard?dal=&al=` | A | Indicatori del periodo | RF19 |

## Esempi

### Login

```http
POST /api/v1/auth/login
Content-Type: application/json

{ "email": "giulia@example.com", "password": "********" }
```

```json
{ "access_token": "eyJhbGciOi...", "token_type": "bearer", "scade_tra_minuti": 60 }
```

### Prenotazione con sconto Under 26

```http
POST /api/v1/prenotazioni
Authorization: Bearer eyJhbGciOi...
Content-Type: application/json

{ "sessione_id": 42, "codice_promo": null }
```

```json
{
  "id": 318,
  "stato": "in_attesa",
  "servizio": "Esperienza giornaliera – tornio",
  "inizio": "2026-11-07T10:00:00+01:00",
  "prezzo_listino_cent": 6000,
  "sconto_cent": 600,
  "prezzo_finale_cent": 5400,
  "promozione": "Giovani in bottega (-10%)"
}
```

### Dashboard amministratore

```http
GET /api/v1/admin/dashboard?dal=2026-11-01&al=2026-11-30
Authorization: Bearer eyJhbGciOi...
```

```json
{
  "prenotazioni_confermate": 0,
  "tasso_riempimento_medio": 0.0,
  "incassi_cent_per_tipo": { "corso": 0, "esperienza": 0, "coworking": 0, "pacchetto": 0 },
  "membership_attive": 0,
  "valutazione_media": null
}
```

I valori dell'esempio sono a zero: la risposta reale dipende dai dati presenti nel database.
