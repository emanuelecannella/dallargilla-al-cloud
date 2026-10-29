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

/**
 * Messaggio leggibile da una risposta di errore.
 * Gli errori delle regole della bottega hanno già un messaggio ({ detail: "..." });
 * quelli di validazione dei dati sono un elenco di campi ({ detail: [{ msg, loc }] }).
 */
export function messaggioErrore(dati) {
  if (typeof dati?.detail === "string") return dati.detail;
  if (Array.isArray(dati?.detail) && dati.detail.length > 0) {
    return dati.detail[0].msg.replace(/^Value error, /, "");
  }
  return "Si è verificato un errore.";
}

/** Chiamata alle API. Con { token } la richiesta viene autenticata, con { corpo } invia dati JSON. */
export async function richiesta(percorso, { metodo = "GET", corpo, token } = {}) {
  const intestazioni = { "Content-Type": "application/json" };
  if (token) intestazioni.Authorization = `Bearer ${token}`;
  let risposta;
  try {
    risposta = await fetch(BASE + percorso, {
      method: metodo,
      headers: intestazioni,
      body: corpo === undefined ? undefined : JSON.stringify(corpo),
    });
  } catch {
    throw new ErroreApi("Il server non è raggiungibile. Riprova tra qualche istante.", "RETE", 0);
  }
  if (risposta.status === 204) return null;
  const dati = await risposta.json().catch(() => null);
  if (!risposta.ok) {
    const codice = dati?.codice ?? (risposta.status === 422 ? "DATI_NON_VALIDI" : "ERRORE");
    throw new ErroreApi(messaggioErrore(dati), codice, risposta.status);
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

export const account = {
  registrazione: (dati) => richiesta("/auth/registrazione", { metodo: "POST", corpo: dati }),
  login: (email, password) => richiesta("/auth/login", { metodo: "POST", corpo: { email, password } }),
  profilo: (token) => richiesta("/utenti/me", { token }),
  aggiornaProfilo: (token, dati) => richiesta("/utenti/me", { metodo: "PATCH", corpo: dati, token }),
};
