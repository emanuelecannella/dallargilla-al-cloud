// Promemoria per l'area personale: quanti giorni mancano a una lezione.
// Scritto da Emanuele Francesco Cannella.

// Restituisce il giorno di calendario a Palermo nel formato "AAAA-MM-GG"
function giornoAPalermo(data) {
  return new Intl.DateTimeFormat("en-CA", { timeZone: "Europe/Rome" }).format(data);
} 


/**
 * Quanti giorni mancano tra oggi e la data della lezione,
 * contando i giorni di calendario e non le ore.
 */
export function giorniMancanti(inizio, adesso = new Date()) {
  const lezione = Date.parse(giornoAPalermo(new Date(inizio)));
  const oggi = Date.parse(giornoAPalermo(adesso));
  return Math.round((lezione - oggi) / 86400000); // 86400000 = millisecondi in un giorno
}


/** Il messaggio da mostrare accanto alla prenotazione */
export function promemoria(inizio, adesso = new Date()) {
  const giorni = giorniMancanti(inizio, adesso);
  if (giorni < 0) return "";
  if (giorni === 0) return "Oggi!";
  if (giorni === 1) return "Domani";
  return `Tra ${giorni} giorni`;
}

