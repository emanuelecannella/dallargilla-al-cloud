# Casi d'uso

Il diagramma riassume chi fa cosa sulla piattaforma. Il Cliente eredita tutto ciò che può fare il
Visitatore; l'Amministratore ha un'area separata. I codici fra parentesi rimandano ai requisiti
in [requisiti.md](../requisiti.md).

```mermaid
flowchart LR
    V([Visitatore])
    C([Cliente])
    A([Amministratore])

    subgraph Piattaforma["Piattaforma Terracotta Viva"]
        UC1[Consulta vetrina e catalogo<br/>RF01-RF03]
        UC2[Verifica date e posti<br/>RF04]
        UC3[Si registra<br/>RF05]
        UC4[Gestisce il profilo<br/>RF06-RF07]
        UC5[Prenota una sessione<br/>RF08]
        UC6[Acquista pacchetto o membership<br/>RF09]
        UC7[Paga e scarica la ricevuta<br/>RF10]
        UC8[Consulta e annulla prenotazioni<br/>RF11-RF12]
        UC9[Lascia una valutazione<br/>RF13]
        UC10[Gestisce offerta e sessioni<br/>RF15-RF16]
        UC11[Consulta gli iscritti<br/>RF17]
        UC12[Gestisce le promozioni<br/>RF18]
        UC13[Consulta la dashboard KPI<br/>RF19]
    end

    V --> UC1
    V --> UC2
    V --> UC3
    C -. eredita .-> V
    C --> UC4
    C --> UC5
    C --> UC6
    C --> UC8
    C --> UC9
    UC5 -. include .-> UC7
    UC6 -. include .-> UC7
    A --> UC10
    A --> UC11
    A --> UC12
    A --> UC13
```

## Specifica dei casi d'uso principali

### UC5 – Prenota una sessione

| Voce | Descrizione |
| --- | --- |
| Attore | Cliente |
| Precondizioni | Il cliente ha effettuato l'accesso; la sessione è futura e ha posti liberi |
| Flusso principale | 1. Il cliente sceglie un corso o un'esperienza dal catalogo. 2. Seleziona una data disponibile. 3. Il sistema mostra il riepilogo con il prezzo, già scontato se si applica la promo Under 26 (RB03). 4. Il cliente conferma. 5. Il sistema registra la prenotazione nello stato "in attesa di pagamento" e scala un posto. 6. Il cliente paga (UC7) e la prenotazione passa a "confermata". |
| Flussi alternativi | 3a. Il cliente inserisce un codice promo: il sistema applica lo sconto più vantaggioso (RB08). 5a. Nel frattempo i posti sono finiti: il sistema avvisa e non registra nulla (RB01). 5b. Il cliente è già iscritto a quella sessione: il sistema rifiuta la richiesta (RB02). |
| Postcondizioni | La prenotazione compare nell'area personale del cliente e nell'elenco iscritti dell'amministratore |

### UC6 – Acquista pacchetto o membership

| Voce | Descrizione |
| --- | --- |
| Attore | Cliente |
| Precondizioni | Il cliente ha effettuato l'accesso |
| Flusso principale | 1. Il cliente sceglie un pacchetto (es. "Giornata in bottega") o una membership di coworking. 2. Il sistema mostra prezzo, contenuto e validità. 3. Il cliente conferma e paga (UC7). 4. Per una membership, il sistema attiva il contatore degli ingressi e la data di scadenza (RB06). |
| Flussi alternativi | 3a. Il pagamento simulato non va a buon fine: l'acquisto resta "in attesa" e il cliente può riprovare. |
| Postcondizioni | Il pacchetto o la membership compare nell'area personale con gli ingressi residui |

### UC13 – Consulta la dashboard KPI

| Voce | Descrizione |
| --- | --- |
| Attore | Amministratore |
| Precondizioni | L'utente ha effettuato l'accesso con ruolo amministratore |
| Flusso principale | 1. L'amministratore apre la dashboard. 2. Il sistema calcola e mostra: prenotazioni del periodo, tasso di riempimento medio delle sessioni, incassi simulati per tipologia di servizio, membership attive, valutazione media. 3. L'amministratore può cambiare il periodo di riferimento. |
| Postcondizioni | Nessuna modifica ai dati: la dashboard è di sola lettura |
