import { useCallback } from "react";
import { Link, useParams } from "react-router-dom";
import { prenotazioni } from "../api/client.js";
import { useAutenticazione } from "../contesti/Autenticazione.jsx";
import { useCaricamento } from "../hooks/useCaricamento.js";
import { euro } from "../utils/formato.js";

const formatoDataOra = new Intl.DateTimeFormat("it-IT", { dateStyle: "long", timeStyle: "short", timeZone: "Europe/Rome" });

// Ricevuta di un pagamento (RF10): visibile solo al cliente che ha pagato e alla titolare
export default function Ricevuta() {
  const { codice } = useParams();
  const { token } = useAutenticazione();
  const carica = useCallback(() => prenotazioni.ricevuta(token, codice), [token, codice]);
  const { dati, errore, inCaricamento } = useCaricamento(carica);

  if (inCaricamento) return <p className="contenitore sezione">Caricamento…</p>;
  if (errore) {
    return (
      <section className="contenitore sezione">
        <h1>Ricevuta non disponibile</h1>
        <p>{errore.message}</p>
        <Link className="pulsante" to="/area-personale">Torna all'area personale</Link>
      </section>
    );
  }
  return (
    <section className="contenitore sezione dettaglio">
      <Link to="/area-personale" className="indietro">← Area personale</Link>
      <article className="ricevuta">
        <h1>Ricevuta</h1>
        <p className="nota">Bottega Terracotta Viva · Centro storico, Palermo</p>
        <dl>
          <div><dt>Codice</dt><dd>{dati.codice_ricevuta}</dd></div>
          <div><dt>Intestatario</dt><dd>{dati.intestatario}</dd></div>
          <div><dt>Descrizione</dt><dd>{dati.descrizione}</dd></div>
          <div><dt>Data</dt><dd>{formatoDataOra.format(new Date(dati.pagato_il))}</dd></div>
          <div><dt>Metodo</dt><dd>{dati.metodo}</dd></div>
          <div className="ricevuta__totale"><dt>Importo</dt><dd>{euro(dati.importo_cent)}</dd></div>
        </dl>
        <p className="nota">Pagamento simulato a scopo dimostrativo: nessun addebito reale.</p>
      </article>
      <button className="pulsante pulsante--secondario non-stampare" onClick={() => window.print()}>Stampa</button>
    </section>
  );
}
