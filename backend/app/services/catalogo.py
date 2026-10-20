"""Logica del catalogo: consultazione dell'offerta e gestione da parte dell'amministratore."""
from datetime import datetime, timedelta, timezone

from fastapi import status
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, selectinload

from app.core.errori import ErroreApplicativo
from app.models import (
    Pacchetto,
    PianoMembership,
    Prenotazione,
    Servizio,
    Sessione,
    StatoPrenotazione,
    StatoSessione,
    TipoServizio,
    Utente,
)
from app.schemas.catalogo import (
    IscrittoOut,
    PacchettoOut,
    ServizioAggiorna,
    ServizioCrea,
    SessioneAggiorna,
    SessioneCrea,
    SessioneOut,
)

# Una prenotazione occupa un posto finché non viene annullata
STATI_ATTIVI = (StatoPrenotazione.in_attesa, StatoPrenotazione.confermata)


def _non_trovato(cosa: str) -> ErroreApplicativo:
    return ErroreApplicativo(status.HTTP_404_NOT_FOUND, "NON_TROVATO", f"{cosa} non trovato")


# --- Servizi --------------------------------------------------------------------

def elenca_servizi(db: Session, tipo: TipoServizio | None = None, solo_attivi: bool = True):
    query = select(Servizio).order_by(Servizio.tipo, Servizio.prezzo_cent)
    if solo_attivi:
        query = query.where(Servizio.attivo.is_(True))
    if tipo is not None:
        query = query.where(Servizio.tipo == tipo)
    return db.scalars(query).all()


def servizio_per_slug(db: Session, slug: str) -> Servizio:
    servizio = db.scalar(select(Servizio).where(Servizio.slug == slug, Servizio.attivo.is_(True)))
    if servizio is None:
        raise _non_trovato("Servizio")
    return servizio


def servizio_per_id(db: Session, servizio_id: int) -> Servizio:
    servizio = db.get(Servizio, servizio_id)
    if servizio is None:
        raise _non_trovato("Servizio")
    return servizio


def crea_servizio(db: Session, dati: ServizioCrea) -> Servizio:
    servizio = Servizio(**dati.model_dump())
    db.add(servizio)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise ErroreApplicativo(
            status.HTTP_409_CONFLICT, "SLUG_GIA_USATO", "Esiste già un servizio con questo indirizzo"
        ) from None
    db.refresh(servizio)
    return servizio


def aggiorna_servizio(db: Session, servizio_id: int, dati: ServizioAggiorna) -> Servizio:
    servizio = servizio_per_id(db, servizio_id)
    for campo, valore in dati.model_dump(exclude_unset=True).items():
        setattr(servizio, campo, valore)
    db.commit()
    db.refresh(servizio)
    return servizio


def disattiva_servizio(db: Session, servizio_id: int) -> None:
    """Un servizio non si cancella mai: si disattiva, così lo storico resta integro."""
    servizio = servizio_per_id(db, servizio_id)
    servizio.attivo = False
    db.commit()


# --- Sessioni -------------------------------------------------------------------

def _posti_occupati(db: Session, sessione_id: int) -> int:
    return db.scalar(
        select(func.count(Prenotazione.id)).where(
            Prenotazione.sessione_id == sessione_id, Prenotazione.stato.in_(STATI_ATTIVI)
        )
    )


def _in_uscita(db: Session, sessione: Sessione) -> SessioneOut:
    return SessioneOut(
        id=sessione.id,
        servizio_id=sessione.servizio_id,
        inizio=sessione.inizio,
        fine=sessione.fine,
        capienza=sessione.capienza,
        posti_residui=max(sessione.capienza - _posti_occupati(db, sessione.id), 0),
        stato=sessione.stato,
    )


def sessioni_future(db: Session, servizio_id: int) -> list[SessioneOut]:
    """Date in programma per un servizio, dalla più vicina, con i posti residui (RF04)."""
    servizio_per_id(db, servizio_id)
    adesso = datetime.now(timezone.utc)
    occupati = (
        select(Prenotazione.sessione_id, func.count(Prenotazione.id).label("n"))
        .where(Prenotazione.stato.in_(STATI_ATTIVI))
        .group_by(Prenotazione.sessione_id)
        .subquery()
    )
    # Una sola query con LEFT JOIN, invece di una query per ogni data
    righe = db.execute(
        select(Sessione, func.coalesce(occupati.c.n, 0))
        .outerjoin(occupati, occupati.c.sessione_id == Sessione.id)
        .where(
            Sessione.servizio_id == servizio_id,
            Sessione.stato == StatoSessione.programmata,
            Sessione.inizio > adesso,
        )
        .order_by(Sessione.inizio)
    ).all()
    return [
        SessioneOut(
            id=s.id, servizio_id=s.servizio_id, inizio=s.inizio, fine=s.fine,
            capienza=s.capienza, posti_residui=max(s.capienza - n, 0), stato=s.stato,
        )
        for s, n in righe
    ]


def crea_sessione(db: Session, dati: SessioneCrea) -> SessioneOut:
    servizio = servizio_per_id(db, dati.servizio_id)
    if not servizio.attivo:
        raise ErroreApplicativo(
            status.HTTP_400_BAD_REQUEST, "SERVIZIO_NON_ATTIVO", "Il servizio non è attivo"
        )
    if dati.inizio <= datetime.now(timezone.utc):
        raise ErroreApplicativo(
            status.HTTP_400_BAD_REQUEST, "DATA_PASSATA", "Non si può pubblicare una data già passata"
        )
    sessione = Sessione(
        servizio_id=servizio.id,
        inizio=dati.inizio,
        fine=dati.fine or dati.inizio + timedelta(minutes=servizio.durata_minuti),
        capienza=dati.capienza or servizio.capienza,
    )
    db.add(sessione)
    db.commit()
    db.refresh(sessione)
    return _in_uscita(db, sessione)


def aggiorna_sessione(db: Session, sessione_id: int, dati: SessioneAggiorna) -> SessioneOut:
    sessione = db.get(Sessione, sessione_id)
    if sessione is None:
        raise _non_trovato("Sessione")
    modifiche = dati.model_dump(exclude_unset=True)

    if "capienza" in modifiche and modifiche["capienza"] < _posti_occupati(db, sessione_id):
        raise ErroreApplicativo(
            status.HTTP_409_CONFLICT,
            "CAPIENZA_INSUFFICIENTE",
            "La nuova capienza è inferiore ai posti già prenotati",
        )
    for campo, valore in modifiche.items():
        setattr(sessione, campo, valore)
    if sessione.fine <= sessione.inizio:
        db.rollback()
        raise ErroreApplicativo(
            status.HTTP_400_BAD_REQUEST, "ORARIO_NON_VALIDO", "L'orario di fine deve seguire l'inizio"
        )
    db.commit()
    db.refresh(sessione)
    return _in_uscita(db, sessione)


def iscritti_sessione(db: Session, sessione_id: int) -> list[IscrittoOut]:
    """Elenco delle persone iscritte a una data, per l'amministratore (RF17)."""
    if db.get(Sessione, sessione_id) is None:
        raise _non_trovato("Sessione")
    righe = db.execute(
        select(Prenotazione, Utente)
        .join(Utente, Utente.id == Prenotazione.utente_id)
        .where(Prenotazione.sessione_id == sessione_id, Prenotazione.stato.in_(STATI_ATTIVI))
        .order_by(Utente.cognome, Utente.nome)
    ).all()
    return [
        IscrittoOut(
            prenotazione_id=p.id, utente_id=u.id, nome=u.nome, cognome=u.cognome,
            email=u.email, stato_prenotazione=p.stato.value,
        )
        for p, u in righe
    ]


# --- Pacchetti e membership -----------------------------------------------------

def elenca_pacchetti(db: Session) -> list[PacchettoOut]:
    pacchetti = db.scalars(
        select(Pacchetto)
        .where(Pacchetto.attivo.is_(True))
        .options(selectinload(Pacchetto.servizi))
        .order_by(Pacchetto.prezzo_cent)
    ).all()
    risultato = []
    for p in pacchetti:
        separato = sum(s.prezzo_cent for s in p.servizi)
        risultato.append(
            PacchettoOut(
                id=p.id, nome=p.nome, slug=p.slug, descrizione=p.descrizione,
                prezzo_cent=p.prezzo_cent, prezzo_separato_cent=separato,
                risparmio_cent=max(separato - p.prezzo_cent, 0),
                servizi=[s for s in p.servizi],
            )
        )
    return risultato


def elenca_piani(db: Session):
    return db.scalars(
        select(PianoMembership)
        .where(PianoMembership.attivo.is_(True))
        .order_by(PianoMembership.prezzo_cent)
    ).all()
