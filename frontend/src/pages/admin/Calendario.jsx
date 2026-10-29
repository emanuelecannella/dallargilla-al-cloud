import { useCallback, useState } from "react";
import { amministrazione, catalogo } from "../../api/client.js";
import { useAutenticazione } from "../../contesti/Autenticazione.jsx";
import { useCaricamento } from "../../hooks/useCaricamento.js";
import { giorno, inizioConFuso, orario, postiLiberi, statoPrenotazione } from "../../utils/formato.js";

// Calendario della titolare: date in programma, iscritti di ogni data (RF17), nuove date e annullamenti (RF16)
export default function Calendario() {
  const { token } = useAutenticazione();
  const carica = useCallback(async () => {
    const servizi = (await amministrazione.servizi(token)).filter((s) => s.attivo);
    const sessioni = await Promise.all(servizi.map((s) => catalogo.sessioni(s.id)));
    const date = servizi
      .flatMap((s, i) => sessioni[i].map((sessione) => ({ ...sessione, servizio: s })))
      .filter((d) => d.stato === "programmata")
      .sort((a, b) => new Date(a.inizio) - new Date(b.inizio));
    return { servizi, date };
  }, [token]);
  const { dati, errore, inCaricamento, ricarica } = useCaricamento(carica);
  const [aperta, setAperta] = useState(null); // { id, iscritti }
  const [messaggio, setMessaggio] = useState(null);

  async function mostraIscritti(id) {
    if (aperta?.id === id) return setAperta(null);
    try {
      setAperta({ id, iscritti: await amministrazione.iscritti(token, id) });
    } catch (e) {
      setMessaggio({ ok: false, testo: e.message });
    }
  }

  async function pubblica(evento) {
    evento.preventDefault();
    const m = new FormData(evento.currentTarget);
    setMessaggio(null);
    try {
      await amministrazione.nuovaSessione(token, Number(m.get("servizio")), inizioConFuso(m.get("data"), m.get("ora")));
      setMessaggio({ ok: true, testo: "Nuova data pubblicata: è già visibile nella vetrina." });
      evento.currentTarget?.reset?.();
      ricarica();
    } catch (e) {
      setMessaggio({ ok: false, testo: e.message });
    }
  }

  async function annulla(d) {
    if (!window.confirm(`Annullare la data del ${giorno(d.inizio)} (${d.servizio.nome})?`)) return;
    try {
      await amministrazione.annullaSessione(token, d.id);
      setMessaggio({ ok: true, testo: "Data annullata: non è più prenotabile." });
      ricarica();
    } catch (e) {
      setMessaggio({ ok: false, testo: e.message });
    }
  }

  if (inCaricamento) return <p>Caricamento del calendario…</p>;
  if (errore) return <p className="avviso avviso--errore">{errore.message}</p>;

  return (
    <section className="blocco">
      <form onSubmit={pubblica} className="modulo modulo--riga">
        <div className="campo">
          <label htmlFor="servizio">Servizio</label>
          <select id="servizio" name="servizio" required>
            {dati.servizi.map((s) => <option key={s.id} value={s.id}>{s.nome}</option>)}
          </select>
        </div>
        <div className="campo"><label htmlFor="data">Giorno</label><input id="data" name="data" type="date" required /></div>
        <div className="campo"><label htmlFor="ora">Ora di inizio</label><input id="ora" name="ora" type="time" required /></div>
        <button className="pulsante" type="submit">Pubblica data</button>
      </form>
      <p className="nota">Durata e posti si prendono dal servizio. Non si possono pubblicare date già passate.</p>
      {messaggio && <p className={`avviso ${messaggio.ok ? "avviso--ok" : "avviso--errore"}`} role="status">{messaggio.testo}</p>}

      <ul className="prenotazioni">
        {dati.date.map((d) => (
          <li key={d.id} className="prenotazione prenotazione--colonna">
            <div className="prenotazione__riga">
              <div>
                <span className="prenotazione__nome">{d.servizio.nome}</span>
                <span className="nota">{giorno(d.inizio)} · {orario(d.inizio, d.fine)}</span>
              </div>
              <div className="prenotazione__lato">
                <span className="nota">{d.capienza - d.posti_residui}/{d.capienza} iscritti · {postiLiberi(d.posti_residui)}</span>
                <button className="link-pulsante" onClick={() => mostraIscritti(d.id)}>
                  {aperta?.id === d.id ? "Nascondi iscritti" : "Iscritti"}
                </button>
                <button className="link-pulsante" onClick={() => annulla(d)}>Annulla data</button>
              </div>
            </div>
            {aperta?.id === d.id && (
              aperta.iscritti.length === 0 ? (
                <p className="nota">Ancora nessun iscritto.</p>
              ) : (
                <table className="tabella">
                  <thead><tr><th>Nome</th><th>Email</th><th>Telefono</th><th>Stato</th></tr></thead>
                  <tbody>
                    {aperta.iscritti.map((i) => (
                      <tr key={i.prenotazione_id}>
                        <td>{i.cognome} {i.nome}</td>
                        <td><a href={`mailto:${i.email}`}>{i.email}</a></td>
                        <td>{i.telefono ? <a href={`tel:${i.telefono}`}>{i.telefono}</a> : "—"}</td>
                        <td>{statoPrenotazione(i.stato_prenotazione)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              )
            )}
          </li>
        ))}
      </ul>
    </section>
  );
}
