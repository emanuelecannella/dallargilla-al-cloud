import { useState } from "react";
import { Link, useLocation } from "react-router-dom";
import { acquisti } from "../api/client.js";
import { useAutenticazione } from "../contesti/Autenticazione.jsx";
import { euro } from "../utils/formato.js";

/**
 * Acquisto di un pacchetto o di una membership (RF09): conferma, pagamento simulato, esito.
 * prodotto = { pacchetto_id } oppure { piano_id }. Lo sconto Under 26 non si applica: il prezzo è già ridotto.
 */
export default function AcquistoProdotto({ prodotto, nome, prezzoCent, dopoAcquisto }) {
  const { token, utente, verifica } = useAutenticazione();
  const posizione = useLocation();
  const [fase, setFase] = useState("chiuso"); // chiuso → riepilogo → pagamento → fatto
  const [acquisto, setAcquisto] = useState(null);
  const [errore, setErrore] = useState(null);

  if (verifica) return null; // si sta ancora controllando l'accesso: niente pulsanti provvisori
  if (!utente) {
    return (
      <Link className="pulsante pulsante--piccolo" to={`/accesso?da=${encodeURIComponent(posizione.pathname)}`}>
        Accedi per acquistare
      </Link>
    );
  }

  async function esegui(azione) {
    setErrore(null);
    try {
      await azione();
    } catch (e) {
      setErrore(e.message);
    }
  }

  const conferma = () =>
    esegui(async () => {
      setAcquisto(await acquisti.crea(token, prodotto));
      setFase("pagamento");
    });

  const paga = (esito) =>
    esegui(async () => {
      await acquisti.paga(token, acquisto.id, esito);
      setFase("fatto");
      dopoAcquisto?.();
    });

  return (
    <div className="acquisto">
      {fase === "chiuso" && (
        <button className="pulsante pulsante--piccolo" onClick={() => setFase("riepilogo")}>Acquista</button>
      )}
      {fase === "riepilogo" && (
        <div className="azioni">
          <span>{nome}: <strong>{euro(prezzoCent)}</strong></span>
          <button className="pulsante pulsante--piccolo" onClick={conferma}>Conferma</button>
          <button className="link-pulsante" onClick={() => setFase("chiuso")}>Annulla</button>
        </div>
      )}
      {fase === "pagamento" && (
        <div className="azioni">
          <button className="pulsante pulsante--piccolo" onClick={() => paga("riuscito")}>Paga {euro(acquisto.prezzo_finale_cent)}</button>
          <button className="link-pulsante" onClick={() => paga("fallito")}>Simula un pagamento rifiutato</button>
        </div>
      )}
      {fase === "fatto" && (
        <p className="avviso avviso--ok">
          Acquisto completato! Lo trovi nella tua <Link to="/area-personale">area personale</Link>.
        </p>
      )}
      {errore && <p className="avviso avviso--errore" role="alert">{errore}</p>}
    </div>
  );
}
