import { useState } from "react";
import { Link, Navigate, useNavigate, useSearchParams } from "react-router-dom";
import Campo from "../components/Campo.jsx";
import { useAutenticazione } from "../contesti/Autenticazione.jsx";

export default function Accesso() {
  const { accedi, utente } = useAutenticazione();
  const [parametri] = useSearchParams();
  const naviga = useNavigate();
  const destinazione = parametri.get("da") || "/area-personale";
  const [errore, setErrore] = useState(null);
  const [invio, setInvio] = useState(false);

  if (utente) return <Navigate to={destinazione} replace />;

  async function invia(evento) {
    evento.preventDefault();
    const modulo = new FormData(evento.currentTarget);
    setErrore(null);
    setInvio(true);
    try {
      await accedi(modulo.get("email"), modulo.get("password"));
      naviga(destinazione, { replace: true });
    } catch (e) {
      setErrore(e.message);
      setInvio(false);
    }
  }

  return (
    <section className="contenitore sezione modulo-pagina">
      <h1>Accedi</h1>
      <p>Entra nella tua area personale per prenotare e ritrovare i tuoi corsi.</p>
      <form onSubmit={invia} className="modulo">
        <Campo id="email" etichetta="Email" type="email" autoComplete="email" required />
        <Campo id="password" etichetta="Password" type="password" autoComplete="current-password" required />
        {errore && <p className="avviso avviso--errore" role="alert">{errore}</p>}
        <button className="pulsante" type="submit" disabled={invio}>{invio ? "Accesso in corso…" : "Accedi"}</button>
      </form>
      <p>Non hai ancora un account? <Link to={`/registrazione?da=${encodeURIComponent(destinazione)}`}>Registrati</Link></p>
    </section>
  );
}
