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

export const prenotazioni = {
  // acquistoId è facoltativo: indica il pacchetto già pagato che copre la prenotazione
  crea: (token, sessioneId, codicePromo, acquistoId = null) =>
    richiesta("/prenotazioni", {
      metodo: "POST",
      token,
      corpo: { sessione_id: sessioneId, codice_promo: codicePromo || null, acquisto_id: acquistoId },
    }),
  mie: (token) => richiesta("/prenotazioni/mie", { token }),
  annulla: (token, id) => richiesta(`/prenotazioni/${id}`, { metodo: "DELETE", token }),
  // Pagamento simulato: nel prototipo si sceglie l'esito per provare anche il rifiuto
  paga: (token, id, esito = "riuscito") =>
    richiesta(`/prenotazioni/${id}/pagamento`, { metodo: "POST", token, corpo: { esito_simulato: esito } }),
  ricevuta: (token, codice) => richiesta(`/pagamenti/${encodeURIComponent(codice)}/ricevuta`, { token }),
};

export const acquisti = {
  // prodotto: { pacchetto_id } oppure { piano_id }
  crea: (token, prodotto, codicePromo) =>
    richiesta("/acquisti", { metodo: "POST", token, corpo: { ...prodotto, codice_promo: codicePromo || null } }),
  miei: (token) => richiesta("/acquisti/miei", { token }),
  paga: (token, id, esito = "riuscito") =>
    richiesta(`/acquisti/${id}/pagamento`, { metodo: "POST", token, corpo: { esito_simulato: esito } }),
};

export const valutazioni = {
  crea: (token, prenotazioneId, voto, commento) =>
    richiesta("/valutazioni", { metodo: "POST", token, corpo: { prenotazione_id: prenotazioneId, voto, commento } }),
};

// Pannello della titolare: tutti gli indirizzi /admin richiedono il ruolo di amministratore
export const amministrazione = {
  dashboard: (token, dal, al) => {
    const parametri = new URLSearchParams();
    if (dal) parametri.set("dal", dal);
    if (al) parametri.set("al", al);
    return richiesta(`/admin/dashboard?${parametri}`, { token });
  },
  servizi: (token) => richiesta("/admin/servizi", { token }),
  iscritti: (token, sessioneId) => richiesta(`/admin/sessioni/${sessioneId}/iscritti`, { token }),
  nuovaSessione: (token, servizioId, inizio) =>
    richiesta("/admin/sessioni", { metodo: "POST", token, corpo: { servizio_id: servizioId, inizio } }),
  annullaSessione: (token, sessioneId) =>
    richiesta(`/admin/sessioni/${sessioneId}`, { metodo: "PATCH", token, corpo: { stato: "annullata" } }),
};
