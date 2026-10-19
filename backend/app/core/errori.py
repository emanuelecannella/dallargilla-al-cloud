"""Errori applicativi con un formato di risposta uniforme.

Ogni errore restituito dalle API ha la forma {"detail": "...", "codice": "..."}:
il messaggio è pensato per l'utente, il codice per il front-end.
"""
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse


class ErroreApplicativo(Exception):
    def __init__(self, stato_http: int, codice: str, messaggio: str) -> None:
        self.stato_http = stato_http
        self.codice = codice
        self.messaggio = messaggio
        super().__init__(messaggio)


def registra_gestori_errori(app: FastAPI) -> None:
    @app.exception_handler(ErroreApplicativo)
    async def gestisci_errore_applicativo(_: Request, errore: ErroreApplicativo) -> JSONResponse:
        return JSONResponse(
            status_code=errore.stato_http,
            content={"detail": errore.messaggio, "codice": errore.codice},
        )
