# Analisi dei requisiti

Questo documento raccoglie l'analisi svolta prima della progettazione: il funzionamento attuale della
bottega, gli attori coinvolti, i requisiti della piattaforma e le regole di business che il software
dovrà rispettare. Ogni requisito ha un codice (RF = funzionale, RNF = non funzionale, RB = regola di
business), richiamato poi nei test e nel report.

## 1. La bottega oggi: il processo "as-is"

*Bottega Terracotta Viva* è un laboratorio di ceramica artigiana con un'aula per i corsi, quattro torni,
un forno elettrico e uno spazio di lavoro condiviso. L'attività è gestita dalla titolare con l'aiuto di
un collaboratore.

Oggi una prenotazione segue questo percorso:

1. il cliente scopre la bottega tramite passaparola o social e scrive in chat privata per chiedere date e prezzi;
2. la titolare controlla la disponibilità su un'agenda cartacea e risponde a mano, spesso a distanza di ore;
3. il posto viene "bloccato" con una nota a matita, senza conferma scritta per il cliente;
4. il pagamento avviene in bottega il giorno del corso, in contanti o con POS;
5. presenze, iscritti e incassi vengono ricopiati a fine mese su un foglio di calcolo.

### Criticità individuate

| Codice | Criticità | Effetto |
| --- | --- | --- |
| C1 | Informazioni sparse fra agenda, chat e foglio di calcolo | Doppie prenotazioni ed errori di trascrizione |
| C2 | Nessuna vetrina online con offerta e prezzi aggiornati | Ogni richiesta richiede una risposta manuale |
| C3 | Prenotazione senza conferma né storico per il cliente | Disdette tardive e posti vuoti non riassegnati |
| C4 | Pagamento solo in sede | Nessuna garanzia sul posto prenotato |
| C5 | Dati sulle attività ricostruiti a mano | Impossibile capire quali corsi rendono di più |
| C6 | Comunicazione poco presente nei canali usati dai giovani | Pubblico giovane difficile da raggiungere |

## 2. Attori

| Attore | Descrizione |
| --- | --- |
| Visitatore | Chiunque navighi il sito senza account. Consulta la vetrina e il catalogo. |
| Cliente | Visitatore registrato. Prenota, paga, gestisce profilo e storico. |
| Amministratore | Titolare o collaboratore. Gestisce offerta, calendario, iscritti e consulta gli indicatori. |

## 3. Requisiti funzionali

### Vetrina e catalogo

| Codice | Requisito | Attore |
| --- | --- | --- |
| RF01 | Consultare le pagine di presentazione: storia, filosofia, spazi della bottega | Visitatore |
| RF02 | Consultare il catalogo di corsi, esperienze giornaliere, pacchetti e membership, con prezzo e descrizione | Visitatore |
| RF03 | Filtrare il catalogo per tipologia (corso, esperienza, pacchetto, coworking) | Visitatore |
| RF04 | Visualizzare il calendario delle date disponibili e i posti residui | Visitatore |

### Account e area personale

| Codice | Requisito | Attore |
| --- | --- | --- |
| RF05 | Registrarsi con nome, cognome, email, password e data di nascita | Visitatore |
| RF06 | Accedere e uscire dall'area personale | Cliente |
| RF07 | Visualizzare e modificare i propri dati personali | Cliente |
| RF08 | Prenotare una data di un corso o di un'esperienza | Cliente |
| RF09 | Acquistare un pacchetto o una membership di coworking | Cliente |
| RF10 | Pagare una prenotazione (pagamento simulato) e consultare la ricevuta | Cliente |
| RF11 | Consultare le proprie prenotazioni future e passate | Cliente |
| RF12 | Annullare una prenotazione nei termini previsti | Cliente |
| RF13 | Lasciare una valutazione e un commento su un'attività svolta | Cliente |
| RF14 | Applicare un codice promozionale al momento dell'acquisto | Cliente |

### Amministrazione

| Codice | Requisito | Attore |
| --- | --- | --- |
| RF15 | Creare, modificare e disattivare corsi, esperienze, pacchetti e membership | Amministratore |
| RF16 | Pubblicare le date (sessioni) con orario e capienza massima | Amministratore |
| RF17 | Consultare gli iscritti di ogni sessione | Amministratore |
| RF18 | Gestire le promozioni e i codici sconto | Amministratore |
| RF19 | Consultare una dashboard con indicatori: prenotazioni, tasso di riempimento, incassi simulati, membership attive, valutazione media | Amministratore |

## 4. Requisiti non funzionali

| Codice | Requisito |
| --- | --- |
| RNF01 | **Sicurezza**: password salvate solo come hash (bcrypt), accesso alle API protetto da token JWT, permessi distinti per ruolo |
| RNF02 | **Privacy**: raccolta dei soli dati necessari e consenso esplicito al trattamento, in linea con il GDPR |
| RNF03 | **Usabilità**: interfaccia responsive, utilizzabile da smartphone, pensata per un pubblico giovane |
| RNF04 | **Prestazioni**: risposta delle API in tempi brevi per le operazioni comuni |
| RNF05 | **Portabilità**: avvio dell'intero sistema con un solo comando tramite Docker Compose |
| RNF06 | **Manutenibilità**: codice organizzato a livelli (router, servizi, modelli), commentato e coperto da test |
| RNF07 | **Integrità dei dati**: vincoli nel database che impediscono di superare la capienza di una sessione |

## 5. Regole di business

| Codice | Regola |
| --- | --- |
| RB01 | Una sessione non accetta prenotazioni oltre la capienza massima |
| RB02 | Un cliente non può prenotare due volte la stessa sessione |
| RB03 | La promo "Giovani in bottega" applica uno sconto del 10% ai clienti con meno di 26 anni, calcolato dalla data di nascita, su corsi ed esperienze |
| RB04 | Il pacchetto "Giornata in bottega" (tornio + decorazione) costa 85 € invece di 95 € |
| RB05 | La cancellazione è gratuita fino a 48 ore prima della sessione; dopo, la prenotazione resta dovuta |
| RB06 | La membership di coworking dà diritto a un numero fisso di ingressi da 2 ore entro la scadenza; gli ingressi non usati decadono |
| RB07 | Si può lasciare una valutazione solo per un'attività a cui si è partecipato |
| RB08 | Gli sconti non sono cumulabili: si applica il più vantaggioso per il cliente |

## 6. Dai problemi ai requisiti

| Criticità | Requisiti che la risolvono |
| --- | --- |
| C1 Informazioni sparse | RF16, RF17, RNF07 |
| C2 Nessuna vetrina | RF01, RF02, RF03, RF04 |
| C3 Nessuna conferma | RF08, RF11, RF12, RB05 |
| C4 Pagamento solo in sede | RF10 |
| C5 Dati non analizzati | RF19 |
| C6 Pubblico giovane | RF13, RF14, RB03, RNF03 |
