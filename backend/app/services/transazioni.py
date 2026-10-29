"""Logica di prenotazioni, acquisti e pagamenti simulati: il cuore della piattaforma."""
import secrets
import string
from datetime import date, datetime, timedelta, timezone
from zoneinfo import ZoneInfo

from fastapi import status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.errori import ErroreApplicativo
from app.models import (
    Acquisto,
    EsitoPagamento,
    Pacchetto,
    Pagamento,
    PianoMembership,
    Prenotazione,
    RuoloUtente,
    Servizio,
    Sessione,
    StatoAcquisto,
    StatoPrenotazione,
    StatoSessione,
    TipoServizio,
    Utente,
)
from app.schemas.transazioni import (
    AcquistoCrea,
    AcquistoOut,
    PagamentoOut,
    PrenotazioneCrea,
    PrenotazioneOut,
    RicevutaOut,
)
from app.services.sconti import migliore_sconto

ORE_CANCELLAZIONE_GRATUITA = 48  # RB05
FUSO_BOTTEGA = ZoneInfo("Europe/Rome")
STATI_ATTIVI = (StatoPrenotazione.in_attesa, StatoPrenotazione.confermata)


def _errore(stato: int, codice: str, messaggio: str) -> ErroreApplicativo:
    return ErroreApplicativo(stato, codice, messaggio)


def _adesso() -> datetime:
    return datetime.now(timezone.utc)


def _codice_ricevuta() -> str:
    alfabeto = string.ascii_uppercase + string.digits
    return "TV-" + "".join(secrets.choice(alfabeto) for _ in range(8))


# --- Conversioni in uscita --------------------------------------------------------

def _annullabile(p: Prenotazione) -> bool:
    """Stessa regola usata da annulla_prenotazione: fino a 48 ore prima dell'inizio (RB05)."""
    return (p.stato != StatoPrenotazione.annullata
            and p.sessione.inizio - _adesso() >= timedelta(hours=ORE_CANCELLAZIONE_GRATUITA))


def prenotazione_out(p: Prenotazione) -> PrenotazioneOut:
    riusciti = [pg for pg in p.pagamenti if pg.esito == EsitoPagamento.riuscito]
    return PrenotazioneOut(
        id=p.id, stato=p.stato, sessione_id=p.sessione_id, servizio=p.sessione.servizio.nome,
        servizio_slug=p.sessione.servizio.slug,
        inizio=p.sessione.inizio, fine=p.sessione.fine, prezzo_listino_cent=p.prezzo_listino_cent,
        sconto_cent=p.sconto_cent, prezzo_finale_cent=p.prezzo_finale_cent,
        promozione=p.promozione.nome if p.promozione else None, acquisto_id=p.acquisto_id,
        codice_ricevuta=riusciti[-1].codice_ricevuta if riusciti else None,
        annullabile=_annullabile(p), creata_il=p.creata_il,
    )


def acquisto_out(a: Acquisto) -> AcquistoOut:
    return AcquistoOut(
        id=a.id, tipo="pacchetto" if a.pacchetto_id else "membership",
        nome=a.pacchetto.nome if a.pacchetto else a.piano.nome, stato=a.stato,
        prezzo_listino_cent=a.prezzo_listino_cent, sconto_cent=a.sconto_cent,
        prezzo_finale_cent=a.prezzo_finale_cent,
        promozione=a.promozione.nome if a.promozione else None,
        ingressi_residui=a.ingressi_residui, scadenza=a.scadenza, creato_il=a.creato_il,
    )


# --- Prenotazioni -------------------------------------------------------------------

def _membership_utilizzabile(db: Session, utente: Utente, giorno: date) -> Acquisto | None:
    """La membership attiva con ingressi residui che scade per prima (si consuma quella)."""
    return db.scalar(
        select(Acquisto)
        .where(
            Acquisto.utente_id == utente.id,
            Acquisto.piano_id.is_not(None),
            Acquisto.stato == StatoAcquisto.attivo,
            Acquisto.ingressi_residui > 0,
            Acquisto.scadenza >= giorno,
        )
        .order_by(Acquisto.scadenza)
        .with_for_update()
    )


def _pacchetto_utilizzabile(db: Session, utente: Utente, acquisto_id: int, servizio: Servizio) -> Acquisto:
    acquisto = db.get(Acquisto, acquisto_id)
    if acquisto is None or acquisto.utente_id != utente.id or acquisto.pacchetto_id is None:
        raise _errore(status.HTTP_404_NOT_FOUND, "NON_TROVATO", "Pacchetto acquistato non trovato")
    if acquisto.stato != StatoAcquisto.attivo:
        raise _errore(status.HTTP_400_BAD_REQUEST, "ACQUISTO_NON_ATTIVO", "Il pacchetto non è ancora stato pagato")
    if servizio not in acquisto.pacchetto.servizi:
        raise _errore(status.HTTP_400_BAD_REQUEST, "SERVIZIO_NON_INCLUSO", "Il servizio non è incluso nel pacchetto")
    gia_usato = db.scalar(
        select(func.count(Prenotazione.id))
        .join(Sessione, Sessione.id == Prenotazione.sessione_id)
        .where(
            Prenotazione.acquisto_id == acquisto.id,
            Sessione.servizio_id == servizio.id,
            Prenotazione.stato.in_(STATI_ATTIVI),
        )
    )
    if gia_usato:
        raise _errore(status.HTTP_409_CONFLICT, "PACCHETTO_GIA_USATO", "Questo servizio del pacchetto è già stato prenotato")
    return acquisto


def crea_prenotazione(db: Session, utente: Utente, dati: PrenotazioneCrea) -> Prenotazione:
    """Prenota un posto in una sessione (RF08).

    La riga della sessione viene bloccata con SELECT ... FOR UPDATE: se due clienti
    tentano di prendere l'ultimo posto nello stesso istante, la seconda richiesta attende
    la fine della prima e trova il conteggio aggiornato. La capienza non può essere superata (RB01).
    """
    sessione = db.scalar(select(Sessione).where(Sessione.id == dati.sessione_id).with_for_update())
    if sessione is None:
        raise _errore(status.HTTP_404_NOT_FOUND, "NON_TROVATO", "Sessione non trovata")
    servizio = sessione.servizio
    if sessione.stato != StatoSessione.programmata or sessione.inizio <= _adesso() or not servizio.attivo:
        raise _errore(status.HTTP_400_BAD_REQUEST, "SESSIONE_NON_PRENOTABILE", "Questa data non è prenotabile")

    esistente = db.scalar(
        select(Prenotazione).where(Prenotazione.utente_id == utente.id, Prenotazione.sessione_id == sessione.id)
    )
    if esistente is not None and esistente.stato in STATI_ATTIVI:
        raise _errore(status.HTTP_409_CONFLICT, "GIA_PRENOTATO", "Hai già una prenotazione per questa data")  # RB02

    occupati = db.scalar(
        select(func.count(Prenotazione.id)).where(
            Prenotazione.sessione_id == sessione.id, Prenotazione.stato.in_(STATI_ATTIVI)
        )
    )
    if occupati >= sessione.capienza:
        raise _errore(status.HTTP_409_CONFLICT, "POSTI_ESAURITI", "Posti esauriti per questa data")  # RB01

    acquisto, promo, sconto = None, None, 0
    listino = servizio.prezzo_cent
    if servizio.tipo == TipoServizio.coworking:
        # Il coworking si prenota solo consumando un ingresso della membership (RB06)
        acquisto = _membership_utilizzabile(db, utente, sessione.inizio.astimezone(FUSO_BOTTEGA).date())
        if acquisto is None:
            raise _errore(status.HTTP_400_BAD_REQUEST, "MEMBERSHIP_RICHIESTA",
                          "Per il coworking serve una membership attiva con ingressi disponibili")
        acquisto.ingressi_residui -= 1
        listino = 0
    elif dati.acquisto_id is not None:
        acquisto = _pacchetto_utilizzabile(db, utente, dati.acquisto_id, servizio)
        listino = 0  # già pagato con il pacchetto
    else:
        promo, sconto = migliore_sconto(db, utente, listino, dati.codice_promo, ammette_under26=True)

    finale = listino - sconto
    stato = StatoPrenotazione.confermata if finale == 0 else StatoPrenotazione.in_attesa

    if esistente is not None:
        # Il vincolo di unicità (RB02) impedisce una seconda riga: si riattiva quella annullata
        prenotazione = esistente
    else:
        prenotazione = Prenotazione(utente_id=utente.id, sessione_id=sessione.id)
        db.add(prenotazione)
    prenotazione.acquisto_id = acquisto.id if acquisto else None
    prenotazione.promozione_id = promo.id if promo else None
    prenotazione.prezzo_listino_cent = listino
    prenotazione.sconto_cent = sconto
    prenotazione.prezzo_finale_cent = finale
    prenotazione.stato = stato
    db.commit()  # il commit rilascia il blocco sulla sessione
    db.refresh(prenotazione)
    return prenotazione


def _prenotazione_del_cliente(db: Session, utente: Utente, prenotazione_id: int) -> Prenotazione:
    prenotazione = db.get(Prenotazione, prenotazione_id)
    if prenotazione is None or prenotazione.utente_id != utente.id:
        # Stessa risposta per "inesistente" e "di un altro cliente": non si rivela nulla
        raise _errore(status.HTTP_404_NOT_FOUND, "NON_TROVATO", "Prenotazione non trovata")
    return prenotazione


def mie_prenotazioni(db: Session, utente: Utente) -> list[Prenotazione]:
    """Prenotazioni del cliente, dalla più lontana nel futuro alla più vecchia (RF11)."""
    return db.scalars(
        select(Prenotazione)
        .join(Sessione, Sessione.id == Prenotazione.sessione_id)
        .where(Prenotazione.utente_id == utente.id)
        .order_by(Sessione.inizio.desc())
    ).all()


def annulla_prenotazione(db: Session, utente: Utente, prenotazione_id: int) -> None:
    """Annullamento gratuito fino a 48 ore prima; dopo, la prenotazione resta dovuta (RF12, RB05)."""
    prenotazione = _prenotazione_del_cliente(db, utente, prenotazione_id)
    if prenotazione.stato == StatoPrenotazione.annullata:
        raise _errore(status.HTTP_409_CONFLICT, "GIA_ANNULLATA", "La prenotazione è già annullata")
    if prenotazione.sessione.inizio - _adesso() < timedelta(hours=ORE_CANCELLAZIONE_GRATUITA):
        raise _errore(status.HTTP_400_BAD_REQUEST, "FUORI_TERMINE",
                      f"La cancellazione è possibile fino a {ORE_CANCELLAZIONE_GRATUITA} ore prima dell'inizio")
    acquisto = prenotazione.acquisto
    if acquisto is not None and acquisto.piano_id is not None:
        acquisto.ingressi_residui += 1  # l'ingresso della membership viene restituito
    prenotazione.stato = StatoPrenotazione.annullata
    db.commit()


# --- Acquisti ----------------------------------------------------------------------

def crea_acquisto(db: Session, utente: Utente, dati: AcquistoCrea) -> Acquisto:
    """Acquisto di un pacchetto o di una membership (RF09). Lo sconto Under 26 non si applica:
    vale per corsi ed esperienze singole (RB03), mentre pacchetti e piani sono già scontati."""
    if dati.pacchetto_id is not None:
        prodotto = db.get(Pacchetto, dati.pacchetto_id)
    else:
        prodotto = db.get(PianoMembership, dati.piano_id)
    if prodotto is None or not prodotto.attivo:
        raise _errore(status.HTTP_404_NOT_FOUND, "NON_TROVATO", "Prodotto non trovato")

    promo, sconto = migliore_sconto(db, utente, prodotto.prezzo_cent, dati.codice_promo, ammette_under26=False)
    acquisto = Acquisto(
        utente_id=utente.id, pacchetto_id=dati.pacchetto_id, piano_id=dati.piano_id,
        promozione_id=promo.id if promo else None, prezzo_listino_cent=prodotto.prezzo_cent,
        sconto_cent=sconto, prezzo_finale_cent=prodotto.prezzo_cent - sconto,
        stato=StatoAcquisto.in_attesa,
    )
    db.add(acquisto)
    db.commit()
    db.refresh(acquisto)
    return acquisto


def miei_acquisti(db: Session, utente: Utente) -> list[Acquisto]:
    return db.scalars(
        select(Acquisto).where(Acquisto.utente_id == utente.id).order_by(Acquisto.creato_il.desc())
    ).all()


def _acquisto_del_cliente(db: Session, utente: Utente, acquisto_id: int) -> Acquisto:
    acquisto = db.get(Acquisto, acquisto_id)
    if acquisto is None or acquisto.utente_id != utente.id:
        raise _errore(status.HTTP_404_NOT_FOUND, "NON_TROVATO", "Acquisto non trovato")
    return acquisto


# --- Pagamenti simulati ------------------------------------------------------------

def _registra_pagamento(db: Session, importo: int, esito: EsitoPagamento, **oggetto) -> Pagamento:
    pagamento = Pagamento(importo_cent=importo, esito=esito, codice_ricevuta=_codice_ricevuta(), **oggetto)
    db.add(pagamento)
    return pagamento


def _esito(db: Session, pagamento: Pagamento) -> PagamentoOut:
    db.commit()
    db.refresh(pagamento)
    if pagamento.esito == EsitoPagamento.fallito:
        # Il tentativo fallito resta registrato, ma la risposta segnala il rifiuto
        raise _errore(status.HTTP_402_PAYMENT_REQUIRED, "PAGAMENTO_RIFIUTATO",
                      "Pagamento non riuscito: puoi riprovare")
    return PagamentoOut(codice_ricevuta=pagamento.codice_ricevuta, esito=pagamento.esito,
                        importo_cent=pagamento.importo_cent, pagato_il=pagamento.pagato_il)


def paga_prenotazione(db: Session, utente: Utente, prenotazione_id: int, esito: EsitoPagamento) -> PagamentoOut:
    prenotazione = _prenotazione_del_cliente(db, utente, prenotazione_id)
    if prenotazione.stato != StatoPrenotazione.in_attesa:
        raise _errore(status.HTTP_409_CONFLICT, "NON_PAGABILE", "La prenotazione non è in attesa di pagamento")
    pagamento = _registra_pagamento(db, prenotazione.prezzo_finale_cent, esito, prenotazione_id=prenotazione.id)
    if esito == EsitoPagamento.riuscito:
        prenotazione.stato = StatoPrenotazione.confermata
    return _esito(db, pagamento)


def paga_acquisto(db: Session, utente: Utente, acquisto_id: int, esito: EsitoPagamento) -> PagamentoOut:
    acquisto = _acquisto_del_cliente(db, utente, acquisto_id)
    if acquisto.stato != StatoAcquisto.in_attesa:
        raise _errore(status.HTTP_409_CONFLICT, "NON_PAGABILE", "L'acquisto non è in attesa di pagamento")
    pagamento = _registra_pagamento(db, acquisto.prezzo_finale_cent, esito, acquisto_id=acquisto.id)
    if esito == EsitoPagamento.riuscito:
        acquisto.stato = StatoAcquisto.attivo
        if acquisto.piano is not None:
            # La membership parte dal giorno del pagamento (RB06)
            acquisto.ingressi_residui = acquisto.piano.ingressi
            acquisto.scadenza = date.today() + timedelta(days=acquisto.piano.durata_giorni)
    return _esito(db, pagamento)


def ricevuta(db: Session, utente: Utente, codice: str) -> RicevutaOut:
    pagamento = db.scalar(select(Pagamento).where(Pagamento.codice_ricevuta == codice))
    if pagamento is None:
        raise _errore(status.HTTP_404_NOT_FOUND, "NON_TROVATO", "Ricevuta non trovata")
    if pagamento.prenotazione is not None:
        titolare = pagamento.prenotazione.utente
        s = pagamento.prenotazione.sessione
        descrizione = f"{s.servizio.nome} – {s.inizio.astimezone(FUSO_BOTTEGA):%d/%m/%Y %H:%M}"
    else:
        titolare = pagamento.acquisto.utente
        a = pagamento.acquisto
        descrizione = a.pacchetto.nome if a.pacchetto else a.piano.nome
    if titolare.id != utente.id and utente.ruolo != RuoloUtente.admin:
        raise _errore(status.HTTP_404_NOT_FOUND, "NON_TROVATO", "Ricevuta non trovata")
    return RicevutaOut(
        codice_ricevuta=pagamento.codice_ricevuta, intestatario=f"{titolare.nome} {titolare.cognome}",
        descrizione=descrizione, importo_cent=pagamento.importo_cent, metodo=pagamento.metodo,
        esito=pagamento.esito, pagato_il=pagamento.pagato_il,
    )
