import { useCallback } from "react";
import { Link, useParams } from "react-router-dom";
import { catalogo } from "../api/client.js";
import { useCaricamento } from "../hooks/useCaricamento.js";
import { euro, formatoServizio, giorno, orario, postiLiberi } from "../utils/formato.js";

// Scheda di un servizio: descrizione, calendario delle prossime date e recensioni (RF02, RF04, RF13)
export default function Servizio() {
  const { slug } = useParams();

  // Prima serve il servizio (per conoscerne l'id), poi date, recensioni e piani in parallelo
  const carica = useCallback(async () => {
    const servizio = await catalogo.servizio(slug);
    const [sessioni, valutazioni, piani] = await Promise.all([
      catalogo.sessioni(servizio.id),
      catalogo.valutazioni(servizio.id),
      servizio.tipo === "coworking" ? catalogo.pianiMembership() : Promise.resolve([]),
    ]);
    return { servizio, sessioni, valutazioni, piani };
  }, [slug]);

  const { dati, errore, inCaricamento } = useCaricamento(carica);

  if (inCaricamento) return <p className="contenitore sezione">Caricamento…</p>;
  if (errore) {
    return (
      <section className="contenitore sezione">
        <h1>{errore.stato === 404 ? "Servizio non trovato" : "Qualcosa è andato storto"}</h1>
        <p>{errore.stato === 404 ? "Questo servizio non esiste o non è più disponibile." : errore.message}</p>
        <Link className="pulsante" to="/">Torna alla bottega</Link>
      </section>
    );
  }

  const { servizio, sessioni, valutazioni, piani } = dati;
  const coworking = servizio.tipo === "coworking";

  return (
    <article className="contenitore sezione dettaglio">
      <Link to="/#servizi" className="indietro">← Tutti i corsi e le esperienze</Link>
      <h1>{servizio.nome}</h1>
      <p className="dettaglio__descrizione">{servizio.descrizione}</p>

      <dl className="dettaglio__dati">
        <div><dt>Formato</dt><dd>{formatoServizio(servizio)}</dd></div>
        <div><dt>Prezzo</dt><dd>{coworking ? "incluso nella membership" : euro(servizio.prezzo_cent)}</dd></div>
        <div><dt>Partecipanti</dt><dd>massimo {servizio.capienza}</dd></div>
      </dl>
      {!coworking && <p className="nota">Hai meno di 26 anni? Il 10% di sconto si applica da solo al momento della prenotazione.</p>}

      {coworking && piani.length > 0 && (
        <section className="blocco">
          <h2>Le membership</h2>
          <p>Il coworking è riservato a chi ha una membership: ogni turno prenotato usa un ingresso.</p>
          <ul className="piani">
            {piani.map((piano) => (
              <li key={piano.id}>
                <strong>{piano.nome}</strong> · {piano.ingressi} ingressi · {euro(piano.prezzo_cent)}
              </li>
            ))}
          </ul>
        </section>
      )}

      <section className="blocco">
        <h2>Prossime date</h2>
        {servizio.numero_incontri > 1 && (
          <p className="nota">La data indicata è quella del primo incontro: il corso prosegue con {servizio.numero_incontri} incontri in tutto.</p>
        )}
        {sessioni.length === 0 ? (
          <p className="avviso">Al momento non ci sono date in calendario: torna a trovarci presto!</p>
        ) : (
          <ul className="calendario">
            {sessioni.map((s) => (
              <li key={s.id} className={s.posti_residui === 0 ? "esaurita" : ""}>
                <span className="calendario__giorno">{giorno(s.inizio)}</span>
                <span>{orario(s.inizio, s.fine)}</span>
                <span className={`posti ${s.posti_residui <= 1 ? "posti--pochi" : ""}`}>
                  {postiLiberi(s.posti_residui)}
                </span>
              </li>
            ))}
          </ul>
        )}
        <p className="nota">Per prenotare un posto serve un account: l'accesso all'area personale è in arrivo.</p>
      </section>

      <section className="blocco">
        <h2>Cosa dicono di noi</h2>
        {valutazioni.numero === 0 ? (
          <p>Ancora nessuna recensione: potresti essere il primo a lasciarne una dopo l'esperienza!</p>
        ) : (
          <>
            <p className="media">★ {valutazioni.media.toFixed(1)} su 5 · {valutazioni.numero} recensioni</p>
            <ul className="recensioni">
              {valutazioni.valutazioni.map((v) => (
                <li key={v.id}>
                  <span className="stelle" aria-label={`${v.voto} stelle su 5`}>{"★".repeat(v.voto)}</span>
                  {v.commento && <p>“{v.commento}”</p>}
                  <span className="autore">— {v.autore}</span>
                </li>
              ))}
            </ul>
          </>
        )}
      </section>
    </article>
  );
}
