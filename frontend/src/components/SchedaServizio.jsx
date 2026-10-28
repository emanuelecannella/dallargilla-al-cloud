import { euro, formatoServizio } from "../utils/formato.js";

const ETICHETTE = { corso: "Corso", esperienza: "Esperienza", coworking: "Coworking" };

export default function SchedaServizio({ servizio }) {
  const coworking = servizio.tipo === "coworking";
  return (
    <article className="scheda">
      <span className={`etichetta etichetta--${servizio.tipo}`}>{ETICHETTE[servizio.tipo]}</span>
      <h3>{servizio.nome}</h3>
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
    </article>
  );
}
