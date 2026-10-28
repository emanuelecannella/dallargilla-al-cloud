import { catalogo } from "../api/client.js";
import SchedaPacchetto from "../components/SchedaPacchetto.jsx";
import SchedaServizio from "../components/SchedaServizio.jsx";
import { benvenuto, chiSiamo, filosofia } from "../contenuti/bottega.js";
import { useCaricamento } from "../hooks/useCaricamento.js";

// Una sola richiesta per servizi e pacchetti, eseguite in parallelo
const caricaCatalogo = () => Promise.all([catalogo.servizi(), catalogo.pacchetti()]);

export default function Home() {
  const { dati, errore, inCaricamento } = useCaricamento(caricaCatalogo);
  const [servizi, pacchetti] = dati ?? [[], []];

  return (
    <>
      <section className="benvenuto">
        <div className="contenitore">
          <p className="benvenuto__sopratitolo">Laboratorio di ceramica · Palermo</p>
          <h1>{benvenuto.titolo}</h1>
          <p className="benvenuto__testo">{benvenuto.testo}</p>
          <a className="pulsante" href="#servizi">Scopri corsi ed esperienze</a>
        </div>
      </section>

      <section id="chi-siamo" className="sezione contenitore due-colonne">
        <div>
          <h2>Chi siamo</h2>
          <p>{chiSiamo}</p>
        </div>
        <div>
          <h2>La nostra filosofia</h2>
          <p>{filosofia}</p>
        </div>
      </section>

      <section id="servizi" className="sezione contenitore">
        <h2>Corsi ed esperienze</h2>
        {inCaricamento && <p className="avviso">Caricamento del catalogo…</p>}
        {errore && <p className="avviso avviso--errore">{errore.message}</p>}
        {!inCaricamento && !errore && (
          <div className="griglia">
            {servizi.map((servizio) => (
              <SchedaServizio key={servizio.id} servizio={servizio} />
            ))}
            {pacchetti.map((pacchetto) => (
              <SchedaPacchetto key={pacchetto.id} pacchetto={pacchetto} />
            ))}
          </div>
        )}
      </section>
    </>
  );
}
