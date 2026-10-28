// Funzioni di formattazione condivise dalle pagine.
// Gli importi arrivano dalle API in centesimi interi, come sono salvati nel database.

const formatoEuro = new Intl.NumberFormat("it-IT", { style: "currency", currency: "EUR" });

/** 34000 -> "340,00 €" */
export function euro(centesimi) {
  return formatoEuro.format(centesimi / 100);
}

/** 90 -> "1 h 30 min", 120 -> "2 h", 45 -> "45 min" */
export function durata(minuti) {
  const ore = Math.floor(minuti / 60);
  const resto = minuti % 60;
  if (ore === 0) return `${resto} min`;
  return resto === 0 ? `${ore} h` : `${ore} h ${resto} min`;
}

/** Riassunto del formato di un servizio, es. "8 incontri da 2 h" oppure "2 h" */
export function formatoServizio(servizio) {
  const singolo = durata(servizio.durata_minuti);
  return servizio.numero_incontri > 1 ? `${servizio.numero_incontri} incontri da ${singolo}` : singolo;
}
