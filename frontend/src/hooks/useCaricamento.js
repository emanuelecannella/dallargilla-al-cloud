import { useEffect, useState } from "react";

/**
 * Esegue una chiamata alle API al montaggio del componente e ne restituisce lo stato:
 * { dati, errore, inCaricamento }. Evita di ripetere la stessa logica in ogni pagina.
 */
export function useCaricamento(chiamata) {
  const [stato, setStato] = useState({ dati: null, errore: null, inCaricamento: true });

  useEffect(() => {
    let attivo = true; // se il componente scompare prima della risposta, non aggiorniamo nulla
    chiamata()
      .then((dati) => attivo && setStato({ dati, errore: null, inCaricamento: false }))
      .catch((errore) => attivo && setStato({ dati: null, errore, inCaricamento: false }));
    return () => {
      attivo = false;
    };
  }, [chiamata]);

  return stato;
}
