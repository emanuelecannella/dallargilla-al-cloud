"""Popola il database con i dati iniziali di Bottega Terracotta Viva.

Uso:  python -m app.seed      (con Docker: docker compose run --rm backend python -m app.seed)

Lo script è idempotente: se un dato esiste già non viene duplicato, quindi si può
eseguire più volte senza problemi. Crea l'amministratore, il listino, il pacchetto,
i piani di membership, la promozione Under 26 e le date delle prossime settimane.
"""
import os
from datetime import date, datetime, time, timedelta
from zoneinfo import ZoneInfo

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.database import SessioneLocale
from app.core.sicurezza import calcola_hash_password
from app.models import (
    Pacchetto,
    PianoMembership,
    Promozione,
    RegolaPromozione,
    RuoloUtente,
    Servizio,
    Sessione,
    TipoServizio,
    Utente,
)

FUSO = ZoneInfo("Europe/Rome")

SERVIZI = [
    # slug, tipo, nome, incontri, minuti per incontro, prezzo in centesimi, capienza, descrizione
    ("corso-tornio-base", TipoServizio.corso, "Corso di tornio base", 8, 120, 34000, 6,
     "Otto incontri per imparare a centrare l'argilla, aprire, tirare su le pareti e rifinire "
     "ciotole e vasi. Argilla, attrezzi e prima cottura inclusi."),
    ("corso-decorazione", TipoServizio.corso, "Corso di decorazione", 4, 120, 14000, 8,
     "Quattro incontri dedicati a ingobbi, sgraffito e pittura su biscotto, per dare un "
     "carattere personale ai propri pezzi."),
    ("corso-cottura-smaltatura", TipoServizio.corso, "Corso di cottura e smaltatura", 3, 150, 15000, 6,
     "Tre incontri per conoscere smalti, temperature e curve di cottura del forno elettrico, "
     "dalla preparazione dei pezzi all'apertura del forno."),
    ("esperienza-tornio", TipoServizio.esperienza, "Esperienza giornaliera – tornio", 1, 120, 6000, 6,
     "Due ore al tornio, anche senza esperienza: si torna a casa con il proprio pezzo, cotto e "
     "pronto da ritirare dopo due settimane."),
    ("esperienza-decorazione", TipoServizio.esperienza, "Esperienza giornaliera – decorazione", 1, 90, 3500, 8,
     "Un'ora e mezza per decorare un pezzo già cotto scegliendo colori e tecniche."),
    ("coworking", TipoServizio.coworking, "Coworking in bottega", 1, 120, 0, 4,
     "Turni da due ore per lavorare in autonomia con torni, attrezzi e forno. "
     "Riservato ai titolari di una membership."),
]

PIANI = [
    ("Membership 1 mese", 8, 30, 12000),
    ("Membership 3 mesi", 24, 90, 33000),
]


def _crea_admin(db: Session) -> None:
    email = os.getenv("ADMIN_EMAIL", "admin@terracotta-viva.example").lower()
    if db.scalar(select(Utente).where(Utente.email == email)):
        return
    db.add(
        Utente(
            email=email,
            password_hash=calcola_hash_password(os.getenv("ADMIN_PASSWORD", "CambiamiSubito1")),
            nome="Titolare",
            cognome="Terracotta Viva",
            data_nascita=date(1985, 1, 1),
            ruolo=RuoloUtente.admin,
            consenso_privacy=True,
        )
    )


def _crea_servizi(db: Session) -> dict[str, Servizio]:
    servizi = {}
    for slug, tipo, nome, incontri, minuti, prezzo, capienza, descrizione in SERVIZI:
        servizio = db.scalar(select(Servizio).where(Servizio.slug == slug))
        if servizio is None:
            servizio = Servizio(
                slug=slug, tipo=tipo, nome=nome, numero_incontri=incontri, durata_minuti=minuti,
                prezzo_cent=prezzo, capienza=capienza, descrizione=descrizione,
            )
            db.add(servizio)
        servizi[slug] = servizio
    db.flush()
    return servizi


def _crea_pacchetto(db: Session, servizi: dict[str, Servizio]) -> None:
    if db.scalar(select(Pacchetto).where(Pacchetto.slug == "giornata-in-bottega")):
        return
    db.add(
        Pacchetto(
            slug="giornata-in-bottega",
            nome="Giornata in bottega",
            descrizione="Tornio al mattino e decorazione al pomeriggio: la prima giornata ideale "
            "per chi si avvicina alla ceramica.",
            prezzo_cent=8500,
            servizi=[servizi["esperienza-tornio"], servizi["esperienza-decorazione"]],
        )
    )


def _crea_piani(db: Session) -> None:
    for nome, ingressi, giorni, prezzo in PIANI:
        if not db.scalar(select(PianoMembership).where(PianoMembership.nome == nome)):
            db.add(PianoMembership(nome=nome, ingressi=ingressi, durata_giorni=giorni, prezzo_cent=prezzo))


def _crea_promozioni(db: Session) -> None:
    if not db.scalar(select(Promozione).where(Promozione.regola == RegolaPromozione.under26)):
        db.add(
            Promozione(
                nome="Giovani in bottega",
                descrizione="Sconto del 10% su corsi ed esperienze per chi ha meno di 26 anni.",
                regola=RegolaPromozione.under26,
                percentuale=10,
            )
        )


def _crea_calendario(db: Session, servizi: dict[str, Servizio], settimane: int = 4) -> None:
    """Pubblica le date delle prossime settimane, se il calendario è ancora vuoto."""
    if db.scalar(select(Sessione).limit(1)) is not None:
        return
    oggi = date.today()
    prossimo_lunedi = oggi + timedelta(days=7 - oggi.weekday())

    def aggiungi(slug: str, giorno: date, ora: time) -> None:
        servizio = servizi[slug]
        inizio = datetime.combine(giorno, ora, tzinfo=FUSO)
        db.add(Sessione(servizio=servizio, inizio=inizio,
                        fine=inizio + timedelta(minutes=servizio.durata_minuti),
                        capienza=servizio.capienza))

    for s in range(settimane):
        lunedi = prossimo_lunedi + timedelta(weeks=s)
        sabato = lunedi + timedelta(days=5)
        aggiungi("esperienza-tornio", sabato, time(10, 0))
        aggiungi("esperienza-decorazione", sabato, time(12, 30))
        aggiungi("esperienza-tornio", sabato, time(15, 0))
        for giorno in (1, 3):  # martedì e giovedì sera
            aggiungi("coworking", lunedi + timedelta(days=giorno), time(18, 0))
    # I corsi partono il primo mercoledì disponibile (data del primo incontro)
    aggiungi("corso-tornio-base", prossimo_lunedi + timedelta(days=2), time(19, 0))
    aggiungi("corso-decorazione", prossimo_lunedi + timedelta(days=9), time(19, 0))
    aggiungi("corso-cottura-smaltatura", prossimo_lunedi + timedelta(days=16), time(18, 30))


def popola(db: Session) -> None:
    _crea_admin(db)
    servizi = _crea_servizi(db)
    _crea_pacchetto(db, servizi)
    _crea_piani(db)
    _crea_promozioni(db)
    _crea_calendario(db, servizi)
    db.commit()


if __name__ == "__main__":
    with SessioneLocale() as sessione:
        popola(sessione)
    print("Dati iniziali di Bottega Terracotta Viva caricati.")
