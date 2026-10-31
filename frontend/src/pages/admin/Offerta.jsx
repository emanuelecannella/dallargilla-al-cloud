import { useCallback, useState } from "react";
import { amministrazione, offerta } from "../../api/client.js";
import Campo from "../../components/Campo.jsx";
import { useAutenticazione } from "../../contesti/Autenticazione.jsx";
import { useCaricamento } from "../../hooks/useCaricamento.js";
import { euro, euroInCentesimi, formatoServizio, slugDa } from "../../utils/formato.js";

const TIPI = { corso: "Corso", esperienza: "Esperienza", coworking: "Coworking" };

// Gestione dell'offerta (RF15): servizi con prezzi, durate e posti; attivazione e disattivazione
function Servizi({ token, onMessaggio }) {
  const carica = useCallback(() => amministrazione.servizi(token), [token]);
  const { dati, errore, inCaricamento, ricarica } = useCaricamento(carica);
  const [inModifica, setInModifica] = useState(null); // id del servizio aperto, oppure "nuovo"

  async function salva(evento, servizio) {
    evento.preventDefault();
    const m = new FormData(evento.currentTarget);
    const prezzo = euroInCentesimi(m.get("prezzo"));
    if (prezzo === null) return onMessaggio({ ok: false, testo: "Il prezzo non è valido: scrivilo come 35 oppure 35,50." });
    const dati = {
      nome: m.get("nome").trim(),
      descrizione: m.get("descrizione").trim(),
      prezzo_cent: prezzo,
      durata_minuti: Number(m.get("durata")),
      numero_incontri: Number(m.get("incontri")),
      capienza: Number(m.get("capienza")),
    };
    try {
      if (servizio) {
        await offerta.aggiornaServizio(token, servizio.id, dati);
        onMessaggio({ ok: true, testo: `«${dati.nome}» aggiornato: le modifiche sono già in vetrina.` });
      } else {
        await offerta.creaServizio(token, { ...dati, tipo: m.get("tipo"), slug: slugDa(dati.nome) });
        onMessaggio({ ok: true, testo: `«${dati.nome}» creato. Ora pubblica le sue date dal calendario.` });
      }
      setInModifica(null);
      ricarica();
    } catch (e) {
      onMessaggio({ ok: false, testo: e.message });
    }
  }

  async function cambiaStato(servizio) {
    const azione = servizio.attivo ? "disattivare" : "riattivare";
    if (!window.confirm(`Vuoi ${azione} «${servizio.nome}»?`)) return;
    try {
      await offerta.aggiornaServizio(token, servizio.id, { attivo: !servizio.attivo });
      onMessaggio({
        ok: true,
        testo: servizio.attivo
          ? `«${servizio.nome}» non è più visibile né prenotabile. Lo storico resta conservato.`
          : `«${servizio.nome}» è di nuovo in vetrina.`,
      });
      ricarica();
    } catch (e) {
      onMessaggio({ ok: false, testo: e.message });
    }
  }

  const modulo = (s) => (
    <form onSubmit={(e) => salva(e, s)} className="modulo scheda-modifica">
      {!s && (
        <div className="campo">
          <label htmlFor="tipo">Tipologia</label>
          <select id="tipo" name="tipo">
            {Object.entries(TIPI).map(([valore, nome]) => <option key={valore} value={valore}>{nome}</option>)}
          </select>
        </div>
      )}
      <Campo id="nome" etichetta="Nome" defaultValue={s?.nome} required maxLength={120} />
      <div className="campo">
        <label htmlFor="descrizione">Descrizione (si legge in vetrina)</label>
        <textarea id="descrizione" name="descrizione" rows={3} defaultValue={s?.descrizione} />
      </div>
      <div className="modulo__riga modulo__riga--quattro">
        <Campo id="prezzo" etichetta="Prezzo (€)" defaultValue={s ? (s.prezzo_cent / 100).toFixed(2).replace(".", ",") : ""} required inputMode="decimal" />
        <Campo id="durata" etichetta="Minuti per incontro" type="number" min={15} max={600} defaultValue={s?.durata_minuti ?? 120} required />
        <Campo id="incontri" etichetta="Incontri" type="number" min={1} max={52} defaultValue={s?.numero_incontri ?? 1} required />
        <Campo id="capienza" etichetta="Posti" type="number" min={1} max={50} defaultValue={s?.capienza ?? 6} required />
      </div>
      {s && <p className="nota">I nuovi posti valgono per le date pubblicate da ora in poi. Le prenotazioni già fatte mantengono il loro prezzo.</p>}
      <div className="azioni">
        <button className="pulsante" type="submit">{s ? "Salva le modifiche" : "Crea il servizio"}</button>
        <button className="pulsante pulsante--secondario" type="button" onClick={() => setInModifica(null)}>Annulla</button>
      </div>
    </form>
  );

  if (inCaricamento) return <p>Caricamento dei servizi…</p>;
  if (errore) return <p className="avviso avviso--errore">{errore.message}</p>;

  return (
    <section className="blocco">
      <div className="titolo-con-azione">
        <h2>Servizi</h2>
        {inModifica !== "nuovo" && <button className="pulsante pulsante--piccolo" onClick={() => setInModifica("nuovo")}>Nuovo servizio</button>}
      </div>
      {inModifica === "nuovo" && modulo(null)}
      <ul className="prenotazioni">
        {dati.map((s) => (
          <li key={s.id} className={`prenotazione prenotazione--colonna ${s.attivo ? "" : "prenotazione--annullata"}`}>
            <div className="prenotazione__riga">
              <div>
                <span className="prenotazione__nome">{s.nome}</span>
                <span className="nota">
                  {TIPI[s.tipo]} · {formatoServizio(s)} · {s.tipo === "coworking" ? "con membership" : euro(s.prezzo_cent)} · max {s.capienza} posti
                </span>
              </div>
              <div className="prenotazione__lato">
                {!s.attivo && <span className="stato">Disattivato</span>}
                <button className="link-pulsante" onClick={() => setInModifica(inModifica === s.id ? null : s.id)}>Modifica</button>
                <button className="link-pulsante" onClick={() => cambiaStato(s)}>{s.attivo ? "Disattiva" : "Riattiva"}</button>
              </div>
            </div>
            {inModifica === s.id && modulo(s)}
          </li>
        ))}
      </ul>
    </section>
  );
}

// Promozioni (RF18): codici sconto con percentuale e periodo di validità; Under 26 automatica
function Promozioni({ token, onMessaggio }) {
  const carica = useCallback(() => offerta.promozioni(token), [token]);
  const { dati, errore, inCaricamento, ricarica } = useCaricamento(carica);
  const [nuova, setNuova] = useState(false);

  async function crea(evento) {
    evento.preventDefault();
    const m = new FormData(evento.currentTarget);
    try {
      await offerta.creaPromozione(token, {
        nome: m.get("promo_nome").trim(),
        codice: m.get("promo_codice").trim().toUpperCase(),
        percentuale: Number(m.get("promo_percentuale")),
        valida_dal: m.get("promo_dal") || null,
        valida_al: m.get("promo_al") || null,
      });
      onMessaggio({ ok: true, testo: "Promozione creata: i clienti possono usare il codice da subito." });
      setNuova(false);
      ricarica();
    } catch (e) {
      onMessaggio({ ok: false, testo: e.message });
    }
  }

  async function cambiaStato(p) {
    try {
      await offerta.aggiornaPromozione(token, p.id, { attiva: !p.attiva });
      ricarica();
    } catch (e) {
      onMessaggio({ ok: false, testo: e.message });
    }
  }

  const periodo = (p) => {
    const d = (x) => new Date(x).toLocaleDateString("it-IT");
    if (p.valida_dal && p.valida_al) return `dal ${d(p.valida_dal)} al ${d(p.valida_al)}`;
    if (p.valida_al) return `fino al ${d(p.valida_al)}`;
    if (p.valida_dal) return `dal ${d(p.valida_dal)}`;
    return "sempre valida";
  };

  if (inCaricamento) return <p>Caricamento delle promozioni…</p>;
  if (errore) return <p className="avviso avviso--errore">{errore.message}</p>;

  return (
    <section className="blocco">
      <div className="titolo-con-azione">
        <h2>Promozioni</h2>
        {!nuova && <button className="pulsante pulsante--piccolo" onClick={() => setNuova(true)}>Nuovo codice sconto</button>}
      </div>
      {nuova && (
        <form onSubmit={crea} className="modulo scheda-modifica">
          <div className="modulo__riga">
            <Campo id="promo_nome" etichetta="Nome della promozione" placeholder="Es. Natale in bottega" required />
            <Campo id="promo_codice" etichetta="Codice da inserire" placeholder="Es. NATALE10" required minLength={3} maxLength={40}
              pattern="[A-Za-z0-9_\-]+" suggerimento="Solo lettere, numeri, trattino e trattino basso." />
          </div>
          <div className="modulo__riga modulo__riga--quattro">
            <Campo id="promo_percentuale" etichetta="Sconto (%)" type="number" min={1} max={100} defaultValue={10} required />
            <Campo id="promo_dal" etichetta="Valida dal" type="date" />
            <Campo id="promo_al" etichetta="Valida fino al" type="date" />
          </div>
          <p className="nota">Se il cliente ha diritto anche allo sconto Under 26, si applica il più vantaggioso: gli sconti non si sommano.</p>
          <div className="azioni">
            <button className="pulsante" type="submit">Crea la promozione</button>
            <button className="pulsante pulsante--secondario" type="button" onClick={() => setNuova(false)}>Annulla</button>
          </div>
        </form>
      )}
      <ul className="prenotazioni">
        {dati.map((p) => (
          <li key={p.id} className={`prenotazione ${p.attiva ? "" : "prenotazione--annullata"}`}>
            <div>
              <span className="prenotazione__nome">{p.nome} · −{p.percentuale}%</span>
              <span className="nota">
                {p.regola === "under26" ? "Automatica per chi ha meno di 26 anni" : <>Codice <code>{p.codice}</code></>} · {periodo(p)}
              </span>
            </div>
            <div className="prenotazione__lato">
              <span className={`stato ${p.attiva ? "stato--confermata" : ""}`}>{p.attiva ? "Attiva" : "Disattivata"}</span>
              <button className="link-pulsante" onClick={() => cambiaStato(p)}>{p.attiva ? "Disattiva" : "Riattiva"}</button>
            </div>
          </li>
        ))}
      </ul>
    </section>
  );
}

export default function Offerta() {
  const { token } = useAutenticazione();
  const [messaggio, setMessaggio] = useState(null);
  return (
    <>
      {messaggio && <p className={`avviso ${messaggio.ok ? "avviso--ok" : "avviso--errore"}`} role="status">{messaggio.testo}</p>}
      <Servizi token={token} onMessaggio={setMessaggio} />
      <Promozioni token={token} onMessaggio={setMessaggio} />
    </>
  );
}
