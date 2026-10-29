import { useCallback, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { acquisti, catalogo, prenotazioni } from "../api/client.js";
import AcquistoProdotto from "../components/AcquistoProdotto.jsx";
import PannelloPrenotazione from "../components/PannelloPrenotazione.jsx";
import { useAutenticazione } from "../contesti/Autenticazione.jsx";
import { useCaricamento } from "../hooks/useCaricamento.js";
import { euro, formatoServizio, giorno, orario, postiLiberi } from "../utils/formato.js";

// Scheda di un servizio: descrizione, calendario delle prossime date e recensioni (RF02, RF04, RF13)
export default function Servizio() {
  const { slug } = useParams();
  const { utente, token } = useAutenticazione();
  const [scelta, setScelta] = useState(null); // la data per cui è aperto il pannello di prenotazione

  // Prima serve il servizio (per conoscerne l'id), poi date, recensioni e piani in parallelo
  const carica = useCallback(async () => {
    const servizio = await catalogo.servizio(slug);
    const [sessioni, valutazioni, piani, mie, miei] = await Promise.all([
      catalogo.sessioni(servizio.id),
      catalogo.valutazioni(servizio.id),
      servizio.tipo === "coworking" ? catalogo.pianiMembership() : Promise.resolve([]),
      token ? prenotazioni.mie(token) : Promise.resolve([]),
      token ? acquisti.miei(token) : Promise.resolve([]),
    ]);
    // Le date in cui il cliente ha già una prenotazione attiva
    const giaPrenotate = new Set(mie.filter((p) => p.stato !== "annullata").map((p) => p.sessione_id));
    // Pacchetti pagati che includono questo servizio e non l'hanno ancora usato
    const pacchetti = miei.filter((a) => a.stato === "attivo" && a.servizi_da_prenotare.includes(servizio.slug));
    const membership = miei.filter((a) => a.tipo === "membership" && a.stato === "attivo");
    return { servizio, sessioni, valutazioni, piani, giaPrenotate, pacchetti, membership };
  }, [slug, token]);

  const { dati, errore, inCaricamento, ricarica } = useCaricamento(carica);

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

  const { servizio, sessioni, valutazioni, piani, giaPrenotate, pacchetti, membership } = dati;
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
          {membership.map((m) => (
            <p key={m.id} className="avviso avviso--ok">
              La tua {m.nome} è attiva: {m.ingressi_residui} ingressi rimasti, valida fino al{" "}
              {new Date(m.scadenza).toLocaleDateString("it-IT")}.
            </p>
          ))}
          <ul className="piani">
            {piani.map((piano) => (
              <li key={piano.id}>
                <span><strong>{piano.nome}</strong> · {piano.ingressi} ingressi in {piano.durata_giorni} giorni · {euro(piano.prezzo_cent)}</span>
                <AcquistoProdotto prodotto={{ piano_id: piano.id }} nome={piano.nome} prezzoCent={piano.prezzo_cent} dopoAcquisto={ricarica} />
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
                {utente && (
                  <span className="calendario__azione">
                    {giaPrenotate.has(s.id) ? (
                      <Link to="/area-personale" className="etichetta etichetta--esperienza">Prenotato ✓</Link>
                    ) : (
                      <button className="pulsante pulsante--piccolo" disabled={s.posti_residui === 0}
                        onClick={() => setScelta(s)}>Prenota</button>
                    )}
                  </span>
                )}
              </li>
            ))}
          </ul>
        )}
        {scelta && (
          <PannelloPrenotazione sessione={scelta} servizio={servizio} pacchetti={pacchetti}
            onChiudi={() => setScelta(null)} onPrenotata={ricarica} />
        )}
        {!utente && (
          <p className="nota">
            Per prenotare un posto <Link to={`/accesso?da=/servizi/${servizio.slug}`}>accedi</Link> oppure{" "}
            <Link to={`/registrazione?da=/servizi/${servizio.slug}`}>crea un account</Link>.
          </p>
        )}
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
