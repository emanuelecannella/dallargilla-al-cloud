import { Link } from "react-router-dom";

export default function Intestazione() {
  return (
    <header className="intestazione">
      <div className="contenitore intestazione__riga">
        <Link to="/" className="marchio">
          Terracotta <span>Viva</span>
        </Link>
        <nav aria-label="Navigazione principale">
          <Link to="/#chi-siamo">Chi siamo</Link>
          <Link to="/#servizi">Corsi ed esperienze</Link>
        </nav>
      </div>
    </header>
  );
}
