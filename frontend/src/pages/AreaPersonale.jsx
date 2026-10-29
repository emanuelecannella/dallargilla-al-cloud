import { useState } from "react";
import Campo from "../components/Campo.jsx";
import { useAutenticazione } from "../contesti/Autenticazione.jsx";

const formatoData = new Intl.DateTimeFormat("it-IT", { day: "numeric", month: "long", year: "numeric" });

// Area personale del cliente (RF07). Prenotazioni, acquisti e ricevute arrivano nei prossimi passi.
export default function AreaPersonale() {
  const { utente, aggiornaProfilo } = useAutenticazione();
  const [modifica, setModifica] = useState(false);
  const [esito, setEsito] = useState(null);

  async function salva(evento) {
    evento.preventDefault();
    const m = new FormData(evento.currentTarget);
    setEsito(null);
    try {
      await aggiornaProfilo({ nome: m.get("nome"), cognome: m.get("cognome"), telefono: m.get("telefono") });
      setModifica(false);
      setEsito({ ok: true, testo: "Dati aggiornati." });
    } catch (e) {
      setEsito({ ok: false, testo: e.message });
    }
  }

  return (
    <section className="contenitore sezione dettaglio">
      <h1>Ciao {utente.nome}!</h1>
      <p>Questa è la tua area personale: qui ritroverai le tue prenotazioni, i tuoi corsi e le ricevute.</p>

      <section className="blocco">
        <h2>I tuoi dati</h2>
        {!modifica ? (
          <>
            <dl className="profilo">
              <div><dt>Nome e cognome</dt><dd>{utente.nome} {utente.cognome}</dd></div>
              <div><dt>Email</dt><dd>{utente.email}</dd></div>
              <div><dt>Telefono</dt><dd>{utente.telefono || "non indicato"}</dd></div>
              <div><dt>Data di nascita</dt><dd>{formatoData.format(new Date(utente.data_nascita))}</dd></div>
            </dl>
            <button className="pulsante pulsante--secondario" onClick={() => setModifica(true)}>Modifica i dati</button>
          </>
        ) : (
          <form onSubmit={salva} className="modulo">
            <div className="modulo__riga">
              <Campo id="nome" etichetta="Nome" defaultValue={utente.nome} required />
              <Campo id="cognome" etichetta="Cognome" defaultValue={utente.cognome} required />
            </div>
            <Campo id="telefono" etichetta="Telefono (facoltativo)" type="tel" defaultValue={utente.telefono ?? ""}
              suggerimento="Lascia vuoto per cancellarlo." />
            <div className="azioni">
              <button className="pulsante" type="submit">Salva</button>
              <button className="pulsante pulsante--secondario" type="button" onClick={() => setModifica(false)}>Annulla</button>
            </div>
          </form>
        )}
        {esito && <p className={`avviso ${esito.ok ? "" : "avviso--errore"}`} role="status">{esito.testo}</p>}
      </section>

      <section className="blocco">
        <h2>Le tue prenotazioni</h2>
        <p className="avviso">Non hai ancora prenotazioni. Scegli un corso o un'esperienza dal catalogo!</p>
      </section>
    </section>
  );
}
