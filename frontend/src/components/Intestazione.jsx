import { Link } from "react-router-dom";

export default function Intestazione() {
  return (
    <header className="intestazione">
      <div className="contenitore intestazione__riga">
        <Link to="/" className="marchio">
          Terracotta <span>Viva</span>
        </Link>
        <nav aria-label="Navigazione principale">
          <a href="/#chi-siamo">Chi siamo</a>
          <a href="/#servizi">Corsi ed esperienze</a>
        </nav>
      </div>
    </header>
  );
}
