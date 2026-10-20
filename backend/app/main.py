"""Punto di ingresso del back-end: crea l'applicazione FastAPI e registra i router."""
from fastapi import APIRouter, Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.config import get_impostazioni
from app.core.database import get_db
from app.core.errori import registra_gestori_errori
from app.routers import admin_catalogo, auth, catalogo, utenti

impostazioni = get_impostazioni()

app = FastAPI(
    title=impostazioni.nome_progetto,
    version="0.3.0",
    description=(
        "API della piattaforma di Bottega Terracotta Viva: catalogo di corsi ed esperienze, "
        "prenotazioni, area personale e pannello di amministrazione."
    ),
)

# Il browser blocca le chiamate verso un'origine diversa dalla pagina, se il server
# non le autorizza esplicitamente (CORS). Autorizziamo solo il front-end.
app.add_middleware(
    CORSMiddleware,
    allow_origins=impostazioni.cors_origini,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

registra_gestori_errori(app)

api = APIRouter(prefix="/api/v1")


@api.get("/salute", tags=["sistema"])
def salute() -> dict[str, str]:
    """Verifica che il server sia attivo."""
    return {"stato": "ok", "servizio": impostazioni.nome_progetto}


@api.get("/salute/database", tags=["sistema"])
def salute_database(db: Session = Depends(get_db)) -> dict[str, str]:
    """Verifica che il server riesca a dialogare con il database."""
    db.execute(text("SELECT 1"))
    return {"stato": "ok", "database": "raggiungibile"}


api.include_router(auth.router)
api.include_router(utenti.router)
api.include_router(catalogo.router)
api.include_router(admin_catalogo.router)

app.include_router(api)
