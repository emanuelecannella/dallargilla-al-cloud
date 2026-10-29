"""Logica di business degli utenti: registrazione, autenticazione, modifica del profilo."""
from fastapi import status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.errori import ErroreApplicativo
from app.core.sicurezza import calcola_hash_password, verifica_password
from app.models import RuoloUtente, Utente
from app.schemas.utente import RegistrazioneIn, UtenteAggiorna


def _normalizza_email(email: str) -> str:
    # Le email non distinguono maiuscole e minuscole: le salviamo sempre in minuscolo
    return email.strip().lower()


def trova_per_email(db: Session, email: str) -> Utente | None:
    return db.scalar(select(Utente).where(Utente.email == _normalizza_email(email)))


def registra_utente(db: Session, dati: RegistrazioneIn) -> Utente:
    if trova_per_email(db, dati.email) is not None:
        raise ErroreApplicativo(
            status.HTTP_409_CONFLICT, "EMAIL_GIA_REGISTRATA", "Esiste già un account con questa email"
        )
    utente = Utente(
        email=_normalizza_email(dati.email),
        password_hash=calcola_hash_password(dati.password),
        nome=dati.nome,
        cognome=dati.cognome,
        data_nascita=dati.data_nascita,
        telefono=dati.telefono,
        ruolo=RuoloUtente.cliente,  # dalla registrazione pubblica nascono solo clienti
        consenso_privacy=dati.consenso_privacy,
    )
    db.add(utente)
    db.commit()
    db.refresh(utente)
    return utente


def autentica(db: Session, email: str, password: str) -> Utente:
    utente = trova_per_email(db, email)
    # Stesso messaggio sia per email inesistente sia per password errata:
    # così non si rivela a un estraneo quali email sono registrate.
    if utente is None or not verifica_password(password, utente.password_hash):
        raise ErroreApplicativo(
            status.HTTP_401_UNAUTHORIZED, "CREDENZIALI_ERRATE", "Email o password non corretti"
        )
    return utente


def aggiorna_profilo(db: Session, utente: Utente, dati: UtenteAggiorna) -> Utente:
    if dati.nome is not None:
        utente.nome = dati.nome.strip()
    if dati.cognome is not None:
        utente.cognome = dati.cognome.strip()
    if dati.data_nascita is not None:
        utente.data_nascita = dati.data_nascita
    if "telefono" in dati.model_fields_set:
        # Si aggiorna solo se il campo è stato inviato; vuoto significa "cancella il numero"
        utente.telefono = dati.telefono

    if dati.nuova_password is not None:
        # Per cambiare password bisogna dimostrare di conoscere quella attuale
        if dati.password_attuale is None or not verifica_password(
            dati.password_attuale, utente.password_hash
        ):
            raise ErroreApplicativo(
                status.HTTP_400_BAD_REQUEST,
                "PASSWORD_ATTUALE_ERRATA",
                "La password attuale non è corretta",
            )
        utente.password_hash = calcola_hash_password(dati.nuova_password)

    db.commit()
    db.refresh(utente)
    return utente
