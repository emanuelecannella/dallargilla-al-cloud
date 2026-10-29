import { useCallback, useState } from "react";
import { Link } from "react-router-dom";
import { prenotazioni } from "../api/client.js";
import { useAutenticazione } from "../contesti/Autenticazione.jsx";
import { useCaricamento } from "../hooks/useCaricamento.js";
import ModuloRecensione from "./ModuloRecensione.jsx";
import { euro, giorno, orario, statoPrenotazione } from "../utils/formato.js";

// Prenotazioni del cliente (RF11): prossime e passate, con pagamento, annullamento e ricevuta
export default function ElencoPrenotazioni() {
  const { token } = useAutenticazione();
  const carica = useCallback(() => prenotazioni.mie(token), [token]);
  const { dati, errore, inCaricamento, ricarica } = useCaricamento(carica);
  const [messaggio, setMessaggio] = useState(null);

  async function azione(fn, testoOk) {
    setMessaggio(null);
    try {
      await fn();
      setMessaggio({ ok: true, testo: testoOk });
    } catch (e) {
      setMessaggio({ ok: false, testo: e.message });
    }
    ricarica();
  }

  if (inCaricamento) return <p>Caricamento delle prenotazioni…</p>;
  if (errore) return <p className="avviso avviso--errore">{errore.message}</p>;

  const adesso = new Date();
  const prossime = dati.filter((p) => new Date(p.inizio) >= adesso).reverse(); // dalla più vicina
  const passate = dati.filter((p) => new Date(p.inizio) < adesso);

  if (dati.length === 0) {
    return (
      <p className="avviso">
        Non hai ancora prenotazioni. Scegli un corso o un'esperienza dal <Link to="/#servizi">catalogo</Link>!
      </p>
    );
  }

  const riga = (p) => (
    <li key={p.id} className={`prenotazione prenotazione--${p.stato}`}>
      <div>
        <Link to={`/servizi/${p.servizio_slug}`} className="prenotazione__nome">{p.servizio}</Link>
        <span className="nota">{giorno(p.inizio)} · {orario(p.inizio, p.fine)}</span>
        <span className="nota">
          {p.acquisto_id ? "Inclusa nel tuo pacchetto o nella tua membership" : euro(p.prezzo_finale_cent)}
          {p.sconto_cent > 0 && ` (sconto ${p.promozione}: −${euro(p.sconto_cent)})`}
        </span>
      </div>
      <div className="prenotazione__lato">
        <span className={`stato stato--${p.stato}`}>{statoPrenotazione(p.stato)}</span>
        {p.stato === "in_attesa" && (
          <button className="pulsante pulsante--piccolo"
            onClick={() => azione(() => prenotazioni.paga(token, p.id), "Pagamento riuscito: prenotazione confermata.")}>
            Paga
          </button>
        )}
        {p.codice_ricevuta && <Link to={`/ricevute/${p.codice_ricevuta}`}>Ricevuta</Link>}
        {p.annullabile && (
          <button className="link-pulsante"
            onClick={() => window.confirm("Vuoi davvero annullare questa prenotazione?") &&
              azione(() => prenotazioni.annulla(token, p.id), "Prenotazione annullata: il posto è di nuovo libero.")}>
            Annulla
          </button>
        )}
        {!p.annullabile && p.stato !== "annullata" && new Date(p.inizio) >= adesso && (
          <small className="nota">Non più annullabile (meno di 48 ore)</small>
        )}
        {p.valutabile && (
          <ModuloRecensione prenotazioneId={p.id}
            dopoInvio={() => { setMessaggio({ ok: true, testo: "Grazie per la tua recensione!" }); ricarica(); }} />
        )}
      </div>
    </li>
  );

  return (
    <>
      {messaggio && <p className={`avviso ${messaggio.ok ? "avviso--ok" : "avviso--errore"}`} role="status">{messaggio.testo}</p>}
      <h3>Prossime</h3>
      {prossime.length ? <ul className="prenotazioni">{prossime.map(riga)}</ul> : <p className="nota">Nessuna prenotazione in arrivo.</p>}
      {passate.length > 0 && (
        <>
          <h3>Passate</h3>
          <ul className="prenotazioni">{passate.map(riga)}</ul>
        </>
      )}
    </>
  );
}
