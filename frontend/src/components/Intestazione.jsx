import { Link, useNavigate } from "react-router-dom";
import { useAutenticazione } from "../contesti/Autenticazione.jsx";

export default function Intestazione() {
  const { utente, esci } = useAutenticazione();
  const naviga = useNavigate();

  function uscita() {
    esci();
    naviga("/");
  }

  return (
    <header className="intestazione">
      <div className="contenitore intestazione__riga">
        <Link to="/" className="marchio">
          Terracotta <span>Viva</span>
        </Link>
        <nav aria-label="Navigazione principale">
          <Link to="/#chi-siamo">Chi siamo</Link>
          <Link to="/#servizi">Corsi ed esperienze</Link>
          {utente ? (
            <>
              <Link to="/area-personale" className="nav__account">Area personale</Link>
              <button type="button" className="nav__esci" onClick={uscita}>Esci</button>
            </>
          ) : (
            <Link to="/accesso" className="nav__account">Accedi</Link>
          )}
        </nav>
      </div>
    </header>
  );
}
