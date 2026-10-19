"""Modelli del dominio.

Importarli tutti qui garantisce che SQLAlchemy e Alembic conoscano ogni tabella.
"""
from app.models.catalogo import Pacchetto, PianoMembership, Servizio, Sessione, pacchetto_servizi
from app.models.enumerazioni import (
    EsitoPagamento,
    RegolaPromozione,
    RuoloUtente,
    StatoAcquisto,
    StatoPrenotazione,
    StatoSessione,
    TipoServizio,
)
from app.models.promozione import Promozione
from app.models.transazioni import Acquisto, Pagamento, Prenotazione
from app.models.utente import Utente
from app.models.valutazione import Valutazione

__all__ = [
    "Acquisto",
    "EsitoPagamento",
    "Pacchetto",
    "Pagamento",
    "PianoMembership",
    "Prenotazione",
    "Promozione",
    "RegolaPromozione",
    "RuoloUtente",
    "Servizio",
    "Sessione",
    "StatoAcquisto",
    "StatoPrenotazione",
    "StatoSessione",
    "TipoServizio",
    "Utente",
    "Valutazione",
    "pacchetto_servizi",
]
