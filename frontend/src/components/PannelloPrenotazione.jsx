import { useEffect, useRef, useState } from "react";
import { Link } from "react-router-dom";
import { prenotazioni } from "../api/client.js";
import { useAutenticazione } from "../contesti/Autenticazione.jsx";
import { euro, giorno, orario } from "../utils/formato.js";

/**
 * Percorso di prenotazione di una data, in tre passi:
 * 1) riepilogo e codice promozionale facoltativo, 2) pagamento simulato, 3) conferma con ricevuta.
 * Il prezzo e lo sconto li calcola sempre il server: il front-end li mostra soltanto.
 */
export default function PannelloPrenotazione({ sessione, servizio, pacchetti = [], onChiudi, onPrenotata }) {
  const { token } = useAutenticazione();
  const [prenotazione, setPrenotazione] = useState(null);
  const [ricevuta, setRicevuta] = useState(null);
  const [errore, setErrore] = useState(null);
  const [attesa, setAttesa] = useState(false);
  const [conPacchetto, setConPacchetto] = useState(pacchetti.length > 0);
  const riquadro = useRef(null);

  // All'apertura il pannello scorre in vista, anche se la data scelta era in cima all'elenco
  useEffect(() => {
    riquadro.current?.scrollIntoView({ behavior: "smooth", block: "center" });
  }, [sessione.id]);

  async function esegui(azione) {
    setErrore(null);
    setAttesa(true);
    try {
      await azione();
    } catch (e) {
      setErrore(e.message);
    } finally {
      setAttesa(false);
    }
  }

  const conferma = (evento) => {
    evento.preventDefault();
    const modulo = new FormData(evento.currentTarget);
    const codice = modulo.get("codice")?.trim();
    const pacchetto = modulo.get("pacchetto"); // "" = paga la singola esperienza
    esegui(async () => {
      const nuova = await prenotazioni.crea(token, sessione.id, codice, pacchetto ? Number(pacchetto) : null);
      setPrenotazione(nuova);
      onPrenotata();
    });
  };

  const paga = (esito) =>
    esegui(async () => {
      const pagamento = await prenotazioni.paga(token, prenotazione.id, esito);
      setRicevuta(pagamento.codice_ricevuta);
      onPrenotata();
    });

  return (
    <div className="pannello" role="dialog" aria-labelledby="titolo-pannello" ref={riquadro}>
      <h3 id="titolo-pannello">{servizio.nome}</h3>
      <p className="nota">{giorno(sessione.inizio)} · {orario(sessione.inizio, sessione.fine)}</p>

      {!prenotazione && (
        <form onSubmit={conferma} className="modulo">
          {servizio.tipo === "coworking" && <p>Il turno usa un ingresso della tua membership attiva.</p>}
          {servizio.tipo !== "coworking" && !conPacchetto && (
            <p>Prezzo di listino: <strong>{euro(servizio.prezzo_cent)}</strong>. Lo sconto Under 26 si applica da solo.</p>
          )}
          {pacchetti.length > 0 && (
            <fieldset className="scelta-pagamento">
              <legend>Come vuoi prenotare?</legend>
              {pacchetti.map((a, i) => (
                <label key={a.id}>
                  <input type="radio" name="pacchetto" value={a.id} defaultChecked={i === 0}
                    onChange={() => setConPacchetto(true)} /> Usa il tuo pacchetto «{a.nome}» (già pagato)
                </label>
              ))}
              <label>
                <input type="radio" name="pacchetto" value="" onChange={() => setConPacchetto(false)} /> Paga questa esperienza a parte
              </label>
            </fieldset>
          )}
          {servizio.tipo !== "coworking" && !conPacchetto && (
            <div className="campo">
              <label htmlFor="codice">Codice promozionale (facoltativo)</label>
              <input id="codice" name="codice" autoComplete="off" />
            </div>
          )}
          <div className="azioni">
            <button className="pulsante" type="submit" disabled={attesa}>Conferma prenotazione</button>
            <button className="pulsante pulsante--secondario" type="button" onClick={onChiudi}>Annulla</button>
          </div>
        </form>
      )}

      {prenotazione && !ricevuta && (
        <>
          <dl className="conto">
            {!prenotazione.acquisto_id && <div><dt>Listino</dt><dd>{euro(prenotazione.prezzo_listino_cent)}</dd></div>}
            {prenotazione.sconto_cent > 0 && (
              <div><dt>Sconto {prenotazione.promozione}</dt><dd>− {euro(prenotazione.sconto_cent)}</dd></div>
            )}
            <div className="conto__totale"><dt>Totale</dt><dd>{euro(prenotazione.prezzo_finale_cent)}</dd></div>
          </dl>
          {prenotazione.stato === "confermata" ? (
            <p className="avviso">Prenotazione confermata: è già inclusa nel tuo pacchetto o nella tua membership.</p>
          ) : (
            <>
              <p className="nota">Il posto è riservato. Pagamento simulato: nel prototipo puoi provare entrambi gli esiti.</p>
              <div className="azioni">
                <button className="pulsante" onClick={() => paga("riuscito")} disabled={attesa}>Paga {euro(prenotazione.prezzo_finale_cent)}</button>
                <button className="pulsante pulsante--secondario" onClick={() => paga("fallito")} disabled={attesa}>Simula un pagamento rifiutato</button>
              </div>
              <p className="nota">Puoi anche pagare più tardi dalla tua <Link to="/area-personale">area personale</Link>.</p>
            </>
          )}
        </>
      )}

      {ricevuta && (
        <div className="avviso avviso--ok">
          <p><strong>Pagamento riuscito, ti aspettiamo in bottega!</strong></p>
          <p>Codice ricevuta: <Link to={`/ricevute/${ricevuta}`}>{ricevuta}</Link></p>
        </div>
      )}

      {errore && <p className="avviso avviso--errore" role="alert">{errore}</p>}
      {(prenotazione || ricevuta) && (
        <button className="pulsante pulsante--secondario" onClick={onChiudi}>Chiudi</button>
      )}
    </div>
  );
}
