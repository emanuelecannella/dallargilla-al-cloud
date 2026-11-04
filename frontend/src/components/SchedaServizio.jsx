import { Link } from "react-router-dom";
import { fotoDi } from "../contenuti/foto.js";
import { euro, formatoServizio } from "../utils/formato.js";

const ETICHETTE = { corso: "Corso", esperienza: "Esperienza", coworking: "Coworking" };

export default function SchedaServizio({ servizio }) {
  const coworking = servizio.tipo === "coworking";
  const foto = fotoDi(servizio.slug);
  return (
    <article className="scheda">
      {foto && <img className="scheda__foto" src={foto.src} alt={foto.alt} width="900" height="675" loading="lazy" />}
      <span className={`etichetta etichetta--${servizio.tipo}`}>{ETICHETTE[servizio.tipo]}</span>
      <h3>
        <Link to={`/servizi/${servizio.slug}`}>{servizio.nome}</Link>
      </h3>
      <p className="scheda__descrizione">{servizio.descrizione}</p>
      <dl className="scheda__dati">
        <div>
          <dt>Durata</dt>
          <dd>{formatoServizio(servizio)}</dd>
        </div>
        <div>
          <dt>Prezzo</dt>
          {/* Il coworking non ha un prezzo a turno: si accede con una membership */}
          <dd>{coworking ? "con membership" : euro(servizio.prezzo_cent)}</dd>
        </div>
        <div>
          <dt>Posti</dt>
          <dd>max {servizio.capienza}</dd>
        </div>
      </dl>
      <Link className="scheda__link" to={`/servizi/${servizio.slug}`}>Scopri le date →</Link>
    </article>
  );
}
