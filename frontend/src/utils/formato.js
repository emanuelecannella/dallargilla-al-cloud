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

// Le date si mostrano sempre nell'ora di Palermo, qualunque sia il fuso del visitatore
const formatoGiorno = new Intl.DateTimeFormat("it-IT", {
  weekday: "long", day: "numeric", month: "long", timeZone: "Europe/Rome",
});
const formatoOra = new Intl.DateTimeFormat("it-IT", {
  hour: "2-digit", minute: "2-digit", timeZone: "Europe/Rome",
});

/** "2026-11-07T10:00:00+01:00" -> "sabato 7 novembre" */
export function giorno(iso) {
  return formatoGiorno.format(new Date(iso));
}

/** Orario di inizio e fine di una sessione: "10:00 – 12:00" */
export function orario(inizio, fine) {
  return `${formatoOra.format(new Date(inizio))} – ${formatoOra.format(new Date(fine))}`;
}

/** Testo dei posti liberi, pensato per far capire subito se affrettarsi */
export function postiLiberi(residui) {
  if (residui <= 0) return "Esaurito";
  if (residui === 1) return "Ultimo posto!";
  return `${residui} posti liberi`;
}
