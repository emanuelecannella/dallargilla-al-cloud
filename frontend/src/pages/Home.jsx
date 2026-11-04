import { catalogo } from "../api/client.js";
import SchedaPacchetto from "../components/SchedaPacchetto.jsx";
import SchedaServizio from "../components/SchedaServizio.jsx";
import { benvenuto, chiSiamo, filosofia } from "../contenuti/bottega.js";
import { fotoBenvenuto, fotoChiSiamo } from "../contenuti/foto.js";
import { useCaricamento } from "../hooks/useCaricamento.js";

// Una sola richiesta per servizi e pacchetti, eseguite in parallelo
const caricaCatalogo = () => Promise.all([catalogo.servizi(), catalogo.pacchetti()]);

export default function Home() {
  const { dati, errore, inCaricamento } = useCaricamento(caricaCatalogo);
  const [servizi, pacchetti] = dati ?? [[], []];

  return (
    <>
      <section className="benvenuto">
        <div className="contenitore benvenuto__griglia">
          <div>
            <p className="benvenuto__sopratitolo">Laboratorio di ceramica · Palermo</p>
            <h1>{benvenuto.titolo}</h1>
            <p className="benvenuto__testo">{benvenuto.testo}</p>
            <a className="pulsante" href="#servizi">Scopri corsi ed esperienze</a>
          </div>
          <img className="benvenuto__foto" src={fotoBenvenuto.src} alt={fotoBenvenuto.alt} width="1600" height="1067" />
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
        <figure className="foto-larga">
          <img src={fotoChiSiamo.src} alt={fotoChiSiamo.alt} width="1600" height="800" loading="lazy" />
          <figcaption>Pezzi tirati al tornio e decorati a mano in laboratorio.</figcaption>
        </figure>
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
