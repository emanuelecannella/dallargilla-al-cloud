"""Dati dimostrativi: clienti inventati, prenotazioni, pagamenti e recensioni.

Uso (dopo app.seed):  python -m app.demo
Con Docker:           docker compose run --rm backend python -m app.demo

Servono a provare la piattaforma come la vedrebbe una bottega già avviata e a
preparare gli screenshot del report: senza questi dati il sito si aprirebbe con un
calendario vuoto e una dashboard a zero. Persone, recensioni e telefoni sono di
fantasia (i numeri iniziano con 000 apposta). Lo script è idempotente: se i clienti
dimostrativi esistono già, non fa nulla.

Le attività future passano dalle stesse funzioni usate dalle API, quindi rispettano
tutte le regole della bottega (posti, sconti, pagamenti). Le attività già svolte,
invece, vengono create direttamente nel database, perché le regole giustamente
impediscono di prenotare una data passata.
"""
from datetime import date, datetime, time, timedelta, timezone
from zoneinfo import ZoneInfo

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.database import SessioneLocale
from app.core.errori import ErroreApplicativo
from app.models import (
    EsitoPagamento,
    Pacchetto,
    Pagamento,
    PianoMembership,
    Prenotazione,
    Promozione,
    RegolaPromozione,
    Servizio,
    Sessione,
    StatoPrenotazione,
    StatoSessione,
    Utente,
)
from app.schemas.amministrazione import ValutazioneCrea
from app.schemas.transazioni import AcquistoCrea, PrenotazioneCrea
from app.schemas.utente import RegistrazioneIn
from app.services.amministrazione import crea_valutazione
from app.services.sconti import migliore_sconto
from app.services.transazioni import (
    _codice_ricevuta,
    crea_acquisto,
    crea_prenotazione,
    paga_acquisto,
    paga_prenotazione,
)
from app.services.utenti import registra_utente

FUSO = ZoneInfo("Europe/Rome")
PASSWORD_DEMO = "Bottega2026"
CODICE_PROMO = "AUTUNNO15"

# chiave, nome, cognome, data di nascita, telefono (finto). Giulia e Luca hanno meno di 26 anni.
CLIENTI = [
    ("giulia", "Giulia", "Rossi", date(2003, 4, 12), "000 000 0001"),
    ("marco", "Marco", "Bianchi", date(1990, 9, 3), "000 000 0002"),
    ("sara", "Sara", "Esposito", date(1997, 1, 25), None),
    ("luca", "Luca", "Ferraro", date(2002, 6, 18), "000 000 0004"),
    ("anna", "Anna", "Greco", date(1985, 11, 30), "000 000 0005"),
]


def _email(chiave: str) -> str:
    return f"{chiave}@demo.terracotta-viva.example"


def _registra_clienti(db: Session) -> dict[str, Utente]:
    clienti = {}
    for chiave, nome, cognome, nascita, telefono in CLIENTI:
        dati = RegistrazioneIn(email=_email(chiave), password=PASSWORD_DEMO, nome=nome, cognome=cognome,
                               data_nascita=nascita, telefono=telefono, consenso_privacy=True)
        clienti[chiave] = registra_utente(db, dati)
    return clienti


def _crea_codice_promo(db: Session) -> None:
    if db.scalar(select(Promozione).where(Promozione.codice == CODICE_PROMO)) is None:
        oggi = date.today()
        db.add(Promozione(codice=CODICE_PROMO, nome="Autunno in bottega",
                          descrizione="15% di sconto per chi prenota in autunno.",
                          regola=RegolaPromozione.codice, percentuale=15,
                          valida_dal=oggi - timedelta(days=10), valida_al=oggi + timedelta(days=30)))
        db.commit()


def _servizio(db: Session, slug: str) -> Servizio:
    return db.scalar(select(Servizio).where(Servizio.slug == slug))


def _prossima_data(db: Session, slug: str) -> Sessione:
    """La prima data futura e prenotabile di un servizio.

    Di solito arriva dal calendario creato da app.seed; se nel frattempo quelle date sono
    passate (per esempio in un database creato settimane prima), ne pubblica una fra una
    settimana, come farebbe la titolare dal pannello.
    """
    sessione = db.scalar(
        select(Sessione).join(Servizio)
        .where(Servizio.slug == slug, Sessione.stato == StatoSessione.programmata,
               Sessione.inizio > datetime.now(timezone.utc) + timedelta(days=2))
        .order_by(Sessione.inizio)
    )
    if sessione is None:
        servizio = _servizio(db, slug)
        inizio = datetime.combine(date.today() + timedelta(days=7), time(18, 0), tzinfo=FUSO)
        sessione = Sessione(servizio=servizio, inizio=inizio,
                            fine=inizio + timedelta(minutes=servizio.durata_minuti), capienza=servizio.capienza)
        db.add(sessione)
        db.commit()
    return sessione


def _data_passata(db: Session, slug: str, giorni_fa: int, ora: time) -> Sessione:
    servizio = _servizio(db, slug)
    inizio = datetime.combine(date.today() - timedelta(days=giorni_fa), ora, tzinfo=FUSO)
    sessione = Sessione(servizio=servizio, inizio=inizio,
                        fine=inizio + timedelta(minutes=servizio.durata_minuti), capienza=servizio.capienza)
    db.add(sessione)
    db.flush()
    return sessione


def _attivita_svolta(db: Session, cliente: Utente, sessione: Sessione, voto: int, commento: str) -> None:
    """Prenotazione già svolta e pagata qualche giorno prima, poi recensita dal cliente."""
    prenotata_il = sessione.inizio - timedelta(days=3)
    listino = sessione.servizio.prezzo_cent
    promo, sconto = migliore_sconto(db, cliente, listino, None, ammette_under26=True,
                                    oggi=prenotata_il.date())
    prenotazione = Prenotazione(utente_id=cliente.id, sessione_id=sessione.id,
                                promozione_id=promo.id if promo else None, prezzo_listino_cent=listino,
                                sconto_cent=sconto, prezzo_finale_cent=listino - sconto,
                                stato=StatoPrenotazione.confermata, creata_il=prenotata_il)
    db.add(prenotazione)
    db.flush()
    db.add(Pagamento(prenotazione_id=prenotazione.id, importo_cent=prenotazione.prezzo_finale_cent,
                     esito=EsitoPagamento.riuscito, codice_ricevuta=_codice_ricevuta(),
                     pagato_il=prenotata_il))
    db.commit()
    # La recensione passa dalla stessa regola delle API: solo attività confermate e già svolte
    crea_valutazione(db, cliente, ValutazioneCrea(prenotazione_id=prenotazione.id, voto=voto,
                                                  commento=commento))


def popola_demo(db: Session) -> bool:
    if _servizio(db, "esperienza-tornio") is None:
        raise SystemExit("Prima carica i dati della bottega con: python -m app.seed")
    if db.scalar(select(Utente).where(Utente.email == _email("giulia"))) is not None:
        return False

    clienti = _registra_clienti(db)
    _crea_codice_promo(db)

    # Attività già svolte, con recensioni (per la vetrina e per la dashboard)
    tornio = _data_passata(db, "esperienza-tornio", giorni_fa=14, ora=time(10, 0))
    decorazione = _data_passata(db, "esperienza-decorazione", giorni_fa=7, ora=time(12, 30))
    _attivita_svolta(db, clienti["giulia"], tornio, 5,
                     "Due ore volate. Ho portato a casa la mia prima ciotola e voglio già tornare!")
    _attivita_svolta(db, clienti["anna"], tornio, 4,
                     "Ambiente accogliente e spiegazioni chiare, anche per chi non ha mai toccato l'argilla.")
    _attivita_svolta(db, clienti["marco"], decorazione, 5,
                     "Un pomeriggio di colori e calma, proprio quello che mi serviva.")
    _attivita_svolta(db, clienti["luca"], decorazione, 4, "")

    # Attività future, con le stesse funzioni delle API
    giulia = crea_prenotazione(db, clienti["giulia"],
                               PrenotazioneCrea(sessione_id=_prossima_data(db, "esperienza-decorazione").id))
    paga_prenotazione(db, clienti["giulia"], giulia.id, EsitoPagamento.riuscito)  # sconto Under 26 automatico

    anna = crea_prenotazione(db, clienti["anna"],
                             PrenotazioneCrea(sessione_id=_prossima_data(db, "corso-tornio-base").id,
                                              codice_promo=CODICE_PROMO))
    paga_prenotazione(db, clienti["anna"], anna.id, EsitoPagamento.riuscito)

    pacchetto = db.scalar(select(Pacchetto).where(Pacchetto.slug == "giornata-in-bottega"))
    acquisto = crea_acquisto(db, clienti["marco"], AcquistoCrea(pacchetto_id=pacchetto.id))
    paga_acquisto(db, clienti["marco"], acquisto.id, EsitoPagamento.riuscito)
    # Marco usa il pacchetto per il tornio; la decorazione resta da prenotare
    crea_prenotazione(db, clienti["marco"],
                      PrenotazioneCrea(sessione_id=_prossima_data(db, "esperienza-tornio").id,
                                       acquisto_id=acquisto.id))

    piano = db.scalar(select(PianoMembership).where(PianoMembership.nome == "Membership 1 mese"))
    membership = crea_acquisto(db, clienti["sara"], AcquistoCrea(piano_id=piano.id))
    paga_acquisto(db, clienti["sara"], membership.id, EsitoPagamento.riuscito)
    crea_prenotazione(db, clienti["sara"], PrenotazioneCrea(sessione_id=_prossima_data(db, "coworking").id))

    # Luca prenota, ma il pagamento viene rifiutato: la prenotazione resta in attesa
    luca = crea_prenotazione(db, clienti["luca"],
                             PrenotazioneCrea(sessione_id=_prossima_data(db, "esperienza-tornio").id))
    try:
        paga_prenotazione(db, clienti["luca"], luca.id, EsitoPagamento.fallito)
    except ErroreApplicativo:
        pass  # è proprio l'esito voluto: il tentativo resta registrato con la sua ricevuta
    return True


if __name__ == "__main__":
    with SessioneLocale() as sessione:
        creati = popola_demo(sessione)
    if creati:
        print("Dati dimostrativi caricati. Clienti di prova (password: " + PASSWORD_DEMO + "):")
        for chiave, nome, cognome, *_ in CLIENTI:
            print(f"  {nome} {cognome}: {_email(chiave)}")
    else:
        print("I dati dimostrativi sono già presenti: nessuna modifica.")
