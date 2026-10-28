import { Link } from "react-router-dom";

export default function NonTrovata() {
  return (
    <section className="sezione contenitore">
      <h1>Pagina non trovata</h1>
      <p>La pagina che cerchi non esiste o è stata spostata.</p>
      <Link className="pulsante" to="/">Torna alla bottega</Link>
    </section>
  );
}
