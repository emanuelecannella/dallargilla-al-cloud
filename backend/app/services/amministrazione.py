"""Valutazioni dei clienti, gestione delle promozioni e indicatori per l'amministratore."""
from datetime import date, datetime, time, timedelta, timezone
from zoneinfo import ZoneInfo

from fastapi import status
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.errori import ErroreApplicativo
from app.models import (
    Acquisto,
    EsitoPagamento,
    Pagamento,
    Prenotazione,
    Promozione,
    RuoloUtente,
    Servizio,
    Sessione,
    StatoAcquisto,
    StatoPrenotazione,
    StatoSessione,
    Utente,
    Valutazione,
)
from app.schemas.amministrazione import (
    DashboardOut,
    PromozioneAggiorna,
    PromozioneCrea,
    RiepilogoValutazioni,
    ServizioPiuRichiesto,
    ValutazioneCrea,
    ValutazioneOut,
)

FUSO_BOTTEGA = ZoneInfo("Europe/Rome")
STATI_ATTIVI = (StatoPrenotazione.in_attesa, StatoPrenotazione.confermata)


def _errore(stato: int, codice: str, messaggio: str) -> ErroreApplicativo:
    return ErroreApplicativo(stato, codice, messaggio)


# --- Valutazioni -------------------------------------------------------------------

def _valutazione_out(v: Valutazione) -> ValutazioneOut:
    p = v.prenotazione
    return ValutazioneOut(id=v.id, voto=v.voto, commento=v.commento, autore=p.utente.nome,
                          servizio=p.sessione.servizio.nome, creata_il=v.creata_il)


def crea_valutazione(db: Session, utente: Utente, dati: ValutazioneCrea) -> ValutazioneOut:
    """Si valuta solo un'attività a cui si è partecipato, una volta sola (RF13, RB07)."""
    prenotazione = db.get(Prenotazione, dati.prenotazione_id)
    if prenotazione is None or prenotazione.utente_id != utente.id:
        raise _errore(status.HTTP_404_NOT_FOUND, "NON_TROVATO", "Prenotazione non trovata")
    if prenotazione.stato != StatoPrenotazione.confermata or prenotazione.sessione.fine > datetime.now(timezone.utc):
        raise _errore(status.HTTP_400_BAD_REQUEST, "NON_VALUTABILE",
                      "Si può valutare solo un'attività confermata e già svolta")
    valutazione = Valutazione(utente_id=utente.id, prenotazione_id=prenotazione.id,
                              voto=dati.voto, commento=dati.commento.strip())
    db.add(valutazione)
    try:
        db.commit()
    except IntegrityError:  # vincolo di unicità sulla prenotazione
        db.rollback()
        raise _errore(status.HTTP_409_CONFLICT, "GIA_VALUTATA", "Hai già valutato questa attività") from None
    db.refresh(valutazione)
    return _valutazione_out(valutazione)


def valutazioni_servizio(db: Session, servizio_id: int) -> RiepilogoValutazioni:
    if db.get(Servizio, servizio_id) is None:
        raise _errore(status.HTTP_404_NOT_FOUND, "NON_TROVATO", "Servizio non trovato")
    valutazioni = db.scalars(
        select(Valutazione)
        .join(Prenotazione, Prenotazione.id == Valutazione.prenotazione_id)
        .join(Sessione, Sessione.id == Prenotazione.sessione_id)
        .where(Sessione.servizio_id == servizio_id)
        .order_by(Valutazione.creata_il.desc())
    ).all()
    media = round(sum(v.voto for v in valutazioni) / len(valutazioni), 2) if valutazioni else None
    return RiepilogoValutazioni(media=media, numero=len(valutazioni),
                                valutazioni=[_valutazione_out(v) for v in valutazioni])


# --- Promozioni ----------------------------------------------------------------------

def elenca_promozioni(db: Session) -> list[Promozione]:
    return db.scalars(select(Promozione).order_by(Promozione.attiva.desc(), Promozione.nome)).all()


def crea_promozione(db: Session, dati: PromozioneCrea) -> Promozione:
    valori = dati.model_dump()
    if valori["codice"]:
        valori["codice"] = valori["codice"].upper()  # i codici si confrontano senza maiuscole/minuscole
    promozione = Promozione(**valori)
    db.add(promozione)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise _errore(status.HTTP_409_CONFLICT, "CODICE_GIA_USATO", "Esiste già una promozione con questo codice") from None
    db.refresh(promozione)
    return promozione


def aggiorna_promozione(db: Session, promozione_id: int, dati: PromozioneAggiorna) -> Promozione:
    promozione = db.get(Promozione, promozione_id)
    if promozione is None:
        raise _errore(status.HTTP_404_NOT_FOUND, "NON_TROVATO", "Promozione non trovata")
    for campo, valore in dati.model_dump(exclude_unset=True).items():
        setattr(promozione, campo, valore)
    if promozione.valida_dal and promozione.valida_al and promozione.valida_al < promozione.valida_dal:
        db.rollback()
        raise _errore(status.HTTP_400_BAD_REQUEST, "DATE_NON_VALIDE", "La data di fine validità precede quella di inizio")
    db.commit()
    db.refresh(promozione)
    return promozione


# --- Dashboard -----------------------------------------------------------------------

def _limiti(dal: date, al: date) -> tuple[datetime, datetime]:
    """Converte un intervallo di giorni (ora italiana) in istanti, fine esclusa."""
    inizio = datetime.combine(dal, time.min, tzinfo=FUSO_BOTTEGA)
    fine = datetime.combine(al + timedelta(days=1), time.min, tzinfo=FUSO_BOTTEGA)
    return inizio, fine


def dashboard(db: Session, dal: date, al: date) -> DashboardOut:
    """Calcola gli indicatori del periodo con poche query aggregate, eseguite dal database."""
    if al < dal:
        raise _errore(status.HTTP_400_BAD_REQUEST, "PERIODO_NON_VALIDO", "La data finale precede quella iniziale")
    t0, t1 = _limiti(dal, al)

    # Prenotazioni confermate per attività che si svolgono nel periodo
    confermate = db.scalar(
        select(func.count(Prenotazione.id))
        .join(Sessione, Sessione.id == Prenotazione.sessione_id)
        .where(Prenotazione.stato == StatoPrenotazione.confermata, Sessione.inizio >= t0, Sessione.inizio < t1)
    )

    # Tasso di riempimento: media, sulle date del periodo, di (posti occupati / capienza)
    occupati = (
        select(Prenotazione.sessione_id, func.count(Prenotazione.id).label("n"))
        .where(Prenotazione.stato.in_(STATI_ATTIVI))
        .group_by(Prenotazione.sessione_id)
        .subquery()
    )
    tasso = db.scalar(
        select(func.avg(func.coalesce(occupati.c.n, 0) * 1.0 / Sessione.capienza))
        .outerjoin(occupati, occupati.c.sessione_id == Sessione.id)
        .where(Sessione.stato == StatoSessione.programmata, Sessione.inizio >= t0, Sessione.inizio < t1)
    )

    # Incassi: pagamenti riusciti nel periodo, divisi per tipo di prodotto
    riusciti = (Pagamento.esito == EsitoPagamento.riuscito, Pagamento.pagato_il >= t0, Pagamento.pagato_il < t1)
    per_tipo: dict[str, int] = {"corso": 0, "esperienza": 0, "coworking": 0, "pacchetto": 0, "membership": 0}
    for tipo, somma in db.execute(
        select(Servizio.tipo, func.sum(Pagamento.importo_cent))
        .join(Prenotazione, Prenotazione.id == Pagamento.prenotazione_id)
        .join(Sessione, Sessione.id == Prenotazione.sessione_id)
        .join(Servizio, Servizio.id == Sessione.servizio_id)
        .where(*riusciti)
        .group_by(Servizio.tipo)
    ):
        per_tipo[tipo.value] = int(somma)
    for e_pacchetto, somma in db.execute(
        select(Acquisto.pacchetto_id.is_not(None), func.sum(Pagamento.importo_cent))
        .join(Acquisto, Acquisto.id == Pagamento.acquisto_id)
        .where(*riusciti)
        .group_by(Acquisto.pacchetto_id.is_not(None))
    ):
        per_tipo["pacchetto" if e_pacchetto else "membership"] = int(somma)

    membership_attive = db.scalar(
        select(func.count(Acquisto.id)).where(
            Acquisto.piano_id.is_not(None), Acquisto.stato == StatoAcquisto.attivo, Acquisto.scadenza >= date.today()
        )
    )
    nuovi_clienti = db.scalar(
        select(func.count(Utente.id)).where(
            Utente.ruolo == RuoloUtente.cliente, Utente.creato_il >= t0, Utente.creato_il < t1
        )
    )
    media_voti = db.scalar(
        select(func.avg(Valutazione.voto)).where(Valutazione.creata_il >= t0, Valutazione.creata_il < t1)
    )
    classifica = db.execute(
        select(Servizio.nome, func.count(Prenotazione.id).label("n"))
        .join(Sessione, Sessione.servizio_id == Servizio.id)
        .join(Prenotazione, Prenotazione.sessione_id == Sessione.id)
        .where(Prenotazione.stato.in_(STATI_ATTIVI), Sessione.inizio >= t0, Sessione.inizio < t1)
        .group_by(Servizio.nome)
        .order_by(func.count(Prenotazione.id).desc(), Servizio.nome)
        .limit(3)
    ).all()

    return DashboardOut(
        dal=dal, al=al, prenotazioni_confermate=confermate,
        tasso_riempimento_medio=round(float(tasso or 0), 3),
        incassi_totali_cent=sum(per_tipo.values()), incassi_cent_per_tipo=per_tipo,
        membership_attive=membership_attive, nuovi_clienti=nuovi_clienti,
        valutazione_media=round(float(media_voti), 2) if media_voti is not None else None,
        servizi_piu_richiesti=[ServizioPiuRichiesto(servizio=nome, prenotazioni=n) for nome, n in classifica],
    )
