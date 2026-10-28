// Unico punto da cui il front-end parla con il back-end.
// Tutte le richieste passano da /api/v1, come stabilito nella specifica delle API.

const BASE = "/api/v1";

/** Errore restituito dalle API: stesso formato per tutti ({ detail, codice }) */
export class ErroreApi extends Error {
  constructor(messaggio, codice, stato) {
    super(messaggio);
    this.codice = codice;
    this.stato = stato;
  }
}

export async function richiesta(percorso, opzioni = {}) {
  let risposta;
  try {
    risposta = await fetch(BASE + percorso, {
      headers: { "Content-Type": "application/json", ...opzioni.headers },
      ...opzioni,
    });
  } catch {
    throw new ErroreApi("Il server non è raggiungibile. Riprova tra qualche istante.", "RETE", 0);
  }
  if (risposta.status === 204) return null;
  const dati = await risposta.json().catch(() => null);
  if (!risposta.ok) {
    const messaggio = typeof dati?.detail === "string" ? dati.detail : "Si è verificato un errore.";
    throw new ErroreApi(messaggio, dati?.codice ?? "ERRORE", risposta.status);
  }
  return dati;
}

export const catalogo = {
  servizi: () => richiesta("/servizi"),
  servizio: (slug) => richiesta(`/servizi/${encodeURIComponent(slug)}`),
  sessioni: (servizioId) => richiesta(`/servizi/${servizioId}/sessioni`),
  valutazioni: (servizioId) => richiesta(`/servizi/${servizioId}/valutazioni`),
  pacchetti: () => richiesta("/pacchetti"),
  pianiMembership: () => richiesta("/piani-membership"),
};
