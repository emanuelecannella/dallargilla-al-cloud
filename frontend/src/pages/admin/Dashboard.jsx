import { useCallback, useState } from "react";
import { amministrazione } from "../../api/client.js";
import { useAutenticazione } from "../../contesti/Autenticazione.jsx";
import { useCaricamento } from "../../hooks/useCaricamento.js";
import { euro, percentuale } from "../../utils/formato.js";

const TIPI = { corso: "Corsi", esperienza: "Esperienze", coworking: "Coworking", pacchetto: "Pacchetti", membership: "Membership" };
const oggi = () => new Date().toISOString().slice(0, 10);
const giorniFa = (n) => new Date(Date.now() - n * 86400000).toISOString().slice(0, 10);

// Indicatori del periodo (RF19): tutti calcolati dal database, qui solo mostrati
export default function Dashboard() {
  const { token } = useAutenticazione();
  const [periodo, setPeriodo] = useState({ dal: giorniFa(29), al: oggi() });
  const carica = useCallback(() => amministrazione.dashboard(token, periodo.dal, periodo.al), [token, periodo]);
  const { dati, errore, inCaricamento } = useCaricamento(carica);

  function cambia(evento) {
    evento.preventDefault();
    const m = new FormData(evento.currentTarget);
    setPeriodo({ dal: m.get("dal"), al: m.get("al") });
  }

  return (
    <section className="blocco">
      <form onSubmit={cambia} className="periodo">
        <label>Dal <input type="date" name="dal" defaultValue={periodo.dal} /></label>
        <label>Al <input type="date" name="al" defaultValue={periodo.al} /></label>
        <button className="pulsante pulsante--piccolo" type="submit">Aggiorna</button>
      </form>

      {inCaricamento && <p>Calcolo degli indicatori…</p>}
      {errore && <p className="avviso avviso--errore">{errore.message}</p>}
      {dati && (
        <>
          <div className="indicatori">
            <div className="indicatore"><span>Incassi</span><strong>{euro(dati.incassi_totali_cent)}</strong></div>
            <div className="indicatore"><span>Prenotazioni confermate</span><strong>{dati.prenotazioni_confermate}</strong></div>
            <div className="indicatore"><span>Riempimento medio delle date</span><strong>{percentuale(dati.tasso_riempimento_medio)}</strong></div>
            <div className="indicatore"><span>Membership attive</span><strong>{dati.membership_attive}</strong></div>
            <div className="indicatore"><span>Nuovi clienti</span><strong>{dati.nuovi_clienti}</strong></div>
            <div className="indicatore"><span>Voto medio</span><strong>{dati.valutazione_media ? `★ ${dati.valutazione_media.toFixed(1)}` : "—"}</strong></div>
          </div>

          <div className="due-colonne">
            <div>
              <h3>Incassi per tipologia</h3>
              <ul className="barre">
                {Object.entries(dati.incassi_cent_per_tipo).map(([tipo, cent]) => {
                  const quota = dati.incassi_totali_cent ? cent / dati.incassi_totali_cent : 0;
                  return (
                    <li key={tipo}>
                      <span>{TIPI[tipo] ?? tipo}</span>
                      <span className="barra"><span style={{ width: percentuale(quota) }} /></span>
                      <span>{euro(cent)}</span>
                    </li>
                  );
                })}
              </ul>
            </div>
            <div>
              <h3>Servizi più richiesti</h3>
              {dati.servizi_piu_richiesti.length === 0 ? (
                <p className="nota">Nessuna prenotazione confermata nel periodo.</p>
              ) : (
                <ol className="classifica">
                  {dati.servizi_piu_richiesti.map((s) => (
                    <li key={s.servizio}>{s.servizio} <span className="nota">· {s.prenotazioni} prenotazioni</span></li>
                  ))}
                </ol>
              )}
            </div>
          </div>
        </>
      )}
    </section>
  );
}
