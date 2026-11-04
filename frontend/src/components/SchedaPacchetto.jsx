import { fotoDi } from "../contenuti/foto.js";
import { euro } from "../utils/formato.js";
import AcquistoProdotto from "./AcquistoProdotto.jsx";

export default function SchedaPacchetto({ pacchetto }) {
  const foto = fotoDi(pacchetto.slug);
  return (
    <article className="scheda scheda--pacchetto">
      {foto && <img className="scheda__foto" src={foto.src} alt={foto.alt} width="900" height="675" loading="lazy" />}
      <span className="etichetta etichetta--pacchetto">Pacchetto</span>
      <h3>{pacchetto.nome}</h3>
      <p className="scheda__descrizione">{pacchetto.descrizione}</p>
      <p className="pacchetto__include">
        Comprende: {pacchetto.servizi.map((s) => s.nome).join(" + ")}
      </p>
      <p className="pacchetto__prezzo">
        <strong>{euro(pacchetto.prezzo_cent)}</strong>{" "}
        <s>{euro(pacchetto.prezzo_separato_cent)}</s>{" "}
        <span className="risparmio">risparmi {euro(pacchetto.risparmio_cent)}</span>
      </p>
      <AcquistoProdotto prodotto={{ pacchetto_id: pacchetto.id }} nome={pacchetto.nome} prezzoCent={pacchetto.prezzo_cent} />
      <p className="nota">Dopo l'acquisto prenoti le due date che preferisci dal calendario di ciascuna esperienza.</p>
    </article>
  );
}
