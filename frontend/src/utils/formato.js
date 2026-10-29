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

const STATI = { in_attesa: "Da pagare", confermata: "Confermata", annullata: "Annullata" };

/** Etichetta leggibile dello stato di una prenotazione */
export function statoPrenotazione(stato) {
  return STATI[stato] ?? stato;
}

/** 0.756 -> "76%" */
export function percentuale(valore) {
  return `${Math.round(valore * 100)}%`;
}

/**
 * Converte data e ora scelte nel modulo (ora di Palermo) nel formato ISO con fuso orario
 * richiesto dalle API, es. ("2026-11-07", "10:00") -> "2026-11-07T10:00:00+01:00".
 * Lo scarto dall'ora UTC dipende dalla stagione: +01:00 in inverno, +02:00 con l'ora legale.
 */
export function inizioConFuso(data, ora) {
  const [a, m, g] = data.split("-").map(Number);
  const [h, min] = ora.split(":").map(Number);
  const comeUtc = Date.UTC(a, m - 1, g, h, min);
  const parti = new Intl.DateTimeFormat("en-GB", {
    timeZone: "Europe/Rome", hourCycle: "h23",
    year: "numeric", month: "2-digit", day: "2-digit", hour: "2-digit", minute: "2-digit",
  }).formatToParts(new Date(comeUtc));
  const v = Object.fromEntries(parti.map((p) => [p.type, p.value]));
  const aRoma = Date.UTC(+v.year, +v.month - 1, +v.day, +v.hour, +v.minute);
  const scarto = Math.round((aRoma - comeUtc) / 60000); // minuti di differenza da UTC
  const segno = scarto >= 0 ? "+" : "-";
  const hh = String(Math.floor(Math.abs(scarto) / 60)).padStart(2, "0");
  const mm = String(Math.abs(scarto) % 60).padStart(2, "0");
  return `${data}T${ora}:00${segno}${hh}:${mm}`;
}
