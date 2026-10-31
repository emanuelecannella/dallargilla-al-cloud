import { useCallback, useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { acquisti } from "../api/client.js";
import { useAutenticazione } from "../contesti/Autenticazione.jsx";
import { useCaricamento } from "../hooks/useCaricamento.js";
import { euro } from "../utils/formato.js";

const STATI = { in_attesa: "Da pagare", attivo: "Attivo", scaduto: "Scaduto" };
const NOMI_SERVIZI = { "esperienza-tornio": "Esperienza al tornio", "esperienza-decorazione": "Esperienza di decorazione" };

// Pacchetti e membership del cliente, con ingressi residui e servizi ancora da prenotare (RF09)
export default function ElencoAcquisti() {
  const { token } = useAutenticazione();
  const carica = useCallback(() => acquisti.miei(token), [token]);
  const { dati, errore, inCaricamento, ricarica } = useCaricamento(carica);
  const [messaggio, setMessaggio] = useState(null);

  // Si aggiorna quando un'azione sulle prenotazioni cambia pacchetti o ingressi
  useEffect(() => {
    window.addEventListener("acquisti-cambiati", ricarica);
    return () => window.removeEventListener("acquisti-cambiati", ricarica);
  }, [ricarica]);

  async function paga(id) {
    setMessaggio(null);
    try {
      await acquisti.paga(token, id);
      setMessaggio({ ok: true, testo: "Pagamento riuscito: il tuo acquisto è attivo." });
    } catch (e) {
      setMessaggio({ ok: false, testo: e.message });
    }
    ricarica();
  }

  if (inCaricamento) return null;
  if (errore) return <p className="avviso avviso--errore">{errore.message}</p>;
  if (dati.length === 0) {
    return <p className="nota">Nessun pacchetto o membership. Li trovi nel <Link to="/#servizi">catalogo</Link>.</p>;
  }

  return (
    <>
      {messaggio && <p className={`avviso ${messaggio.ok ? "avviso--ok" : "avviso--errore"}`} role="status">{messaggio.testo}</p>}
      <ul className="prenotazioni">
        {dati.map((a) => (
          <li key={a.id} className="prenotazione">
            <div>
              <span className="prenotazione__nome">{a.nome}</span>
              <span className="nota">{euro(a.prezzo_finale_cent)}</span>
              {a.tipo === "membership" && a.stato === "attivo" && (
                <span className="nota">
                  {a.ingressi_residui} ingressi rimasti · valida fino al {new Date(a.scadenza).toLocaleDateString("it-IT")}
                </span>
              )}
              {a.tipo === "pacchetto" && a.stato === "attivo" && (
                a.servizi_da_prenotare.length > 0 ? (
                  <span className="nota">
                    Da prenotare:{" "}
                    {a.servizi_da_prenotare.map((slug, i) => (
                      <span key={slug}>{i > 0 && ", "}<Link to={`/servizi/${slug}`}>{NOMI_SERVIZI[slug] ?? slug}</Link></span>
                    ))}
                  </span>
                ) : (
                  <span className="nota">Tutte le esperienze del pacchetto sono prenotate.</span>
                )
              )}
            </div>
            <div className="prenotazione__lato">
              <span className={`stato stato--${a.stato === "attivo" ? "confermata" : a.stato}`}>{STATI[a.stato]}</span>
              {a.codice_ricevuta && <Link to={`/ricevute/${a.codice_ricevuta}`}>Ricevuta</Link>}
              {a.stato === "in_attesa" && (
                <button className="pulsante pulsante--piccolo" onClick={() => paga(a.id)}>Paga</button>
              )}
            </div>
          </li>
        ))}
      </ul>
    </>
  );
}
