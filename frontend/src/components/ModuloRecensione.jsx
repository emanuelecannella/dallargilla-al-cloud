import { useState } from "react";
import { valutazioni } from "../api/client.js";
import { useAutenticazione } from "../contesti/Autenticazione.jsx";

// Recensione di un'attività svolta (RF13): voto da 1 a 5 e commento facoltativo
export default function ModuloRecensione({ prenotazioneId, dopoInvio }) {
  const { token } = useAutenticazione();
  const [aperto, setAperto] = useState(false);
  const [voto, setVoto] = useState(5);
  const [errore, setErrore] = useState(null);

  if (!aperto) {
    return <button className="link-pulsante" onClick={() => setAperto(true)}>Lascia una recensione</button>;
  }

  async function invia(evento) {
    evento.preventDefault();
    const commento = new FormData(evento.currentTarget).get("commento");
    try {
      await valutazioni.crea(token, prenotazioneId, voto, commento);
      dopoInvio();
    } catch (e) {
      setErrore(e.message);
    }
  }

  return (
    <form onSubmit={invia} className="recensione-modulo">
      <div className="stelle-scelta" role="radiogroup" aria-label="Voto">
        {[1, 2, 3, 4, 5].map((n) => (
          <button key={n} type="button" role="radio" aria-checked={voto === n} aria-label={`${n} stelle`}
            className={n <= voto ? "piena" : ""} onClick={() => setVoto(n)}>★</button>
        ))}
      </div>
      <textarea name="commento" rows={3} maxLength={1000} placeholder="Racconta com'è andata (facoltativo)" />
      {errore && <p className="avviso avviso--errore">{errore}</p>}
      <div className="azioni">
        <button className="pulsante pulsante--piccolo" type="submit">Invia</button>
        <button className="link-pulsante" type="button" onClick={() => setAperto(false)}>Annulla</button>
      </div>
    </form>
  );
}
