import { useState } from "react";
import { Link, Navigate, useNavigate, useSearchParams } from "react-router-dom";
import { account } from "../api/client.js";
import Campo from "../components/Campo.jsx";
import { useAutenticazione } from "../contesti/Autenticazione.jsx";

export default function Registrazione() {
  const { accedi, utente } = useAutenticazione();
  const [parametri] = useSearchParams();
  const naviga = useNavigate();
  const destinazione = parametri.get("da") || "/area-personale";
  const [errore, setErrore] = useState(null);
  const [invio, setInvio] = useState(false);

  if (utente) return <Navigate to={destinazione} replace />;

  async function invia(evento) {
    evento.preventDefault();
    const m = new FormData(evento.currentTarget);
    setErrore(null);
    setInvio(true);
    try {
      await account.registrazione({
        nome: m.get("nome"),
        cognome: m.get("cognome"),
        email: m.get("email"),
        telefono: m.get("telefono") || null,
        data_nascita: m.get("data_nascita"),
        password: m.get("password"),
        consenso_privacy: m.get("consenso") === "si",
      });
      // Dopo la registrazione si entra subito, senza dover rifare l'accesso
      await accedi(m.get("email"), m.get("password"));
      naviga(destinazione, { replace: true });
    } catch (e) {
      setErrore(e.message);
      setInvio(false);
    }
  }

  return (
    <section className="contenitore sezione modulo-pagina">
      <h1>Crea il tuo account</h1>
      <p>Bastano pochi dati per prenotare corsi ed esperienze e ritrovarli nella tua area personale.</p>
      <form onSubmit={invia} className="modulo">
        <div className="modulo__riga">
          <Campo id="nome" etichetta="Nome" autoComplete="given-name" required />
          <Campo id="cognome" etichetta="Cognome" autoComplete="family-name" required />
        </div>
        <Campo id="email" etichetta="Email" type="email" autoComplete="email" required />
        <Campo id="telefono" etichetta="Telefono (facoltativo)" type="tel" autoComplete="tel"
          suggerimento="Ci serve solo per avvisarti in caso di imprevisti sulla tua lezione." />
        <Campo id="data_nascita" etichetta="Data di nascita" type="date" required
          suggerimento="Serve per lo sconto Under 26. Per registrarsi servono almeno 14 anni." />
        <Campo id="password" etichetta="Password" type="password" autoComplete="new-password" minLength={8} required
          suggerimento="Almeno 8 caratteri, con almeno una lettera e un numero." />
        <label className="consenso">
          <input type="checkbox" name="consenso" value="si" required />
          <span>
            Acconsento al trattamento dei miei dati personali per la gestione delle prenotazioni, come previsto
            dal Regolamento (UE) 2016/679. I dati non vengono ceduti a terzi.
          </span>
        </label>
        {errore && <p className="avviso avviso--errore" role="alert">{errore}</p>}
        <button className="pulsante" type="submit" disabled={invio}>{invio ? "Registrazione in corso…" : "Registrati"}</button>
      </form>
      <p>Hai già un account? <Link to={`/accesso?da=${encodeURIComponent(destinazione)}`}>Accedi</Link></p>
    </section>
  );
}
