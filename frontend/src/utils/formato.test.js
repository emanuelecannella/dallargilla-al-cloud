import { describe, expect, test } from "vitest";
import { durata, euro, formatoServizio, giorno, orario, euroInCentesimi, inizioConFuso, percentuale, slugDa, postiLiberi, statoPrenotazione } from "./formato.js";

// Lo spazio prima del simbolo dell'euro è uno spazio "non separabile": lo normalizziamo
const pulito = (testo) => testo.replace(/\s/g, " ");

describe("euro", () => {
  test("converte i centesimi in euro con la virgola", () => {
    expect(pulito(euro(34000))).toBe("340,00 €");
    expect(pulito(euro(3500))).toBe("35,00 €");
  });
  test("gestisce i centesimi non tondi e lo zero", () => {
    expect(pulito(euro(5405))).toBe("54,05 €");
    expect(pulito(euro(0))).toBe("0,00 €");
  });
});

describe("durata", () => {
  test("ore intere, ore e minuti, solo minuti", () => {
    expect(durata(120)).toBe("2 h");
    expect(durata(90)).toBe("1 h 30 min");
    expect(durata(45)).toBe("45 min");
  });
});

describe("formatoServizio", () => {
  test("un corso mostra il numero di incontri", () => {
    expect(formatoServizio({ numero_incontri: 8, durata_minuti: 120 })).toBe("8 incontri da 2 h");
  });
  test("un'esperienza mostra solo la durata", () => {
    expect(formatoServizio({ numero_incontri: 1, durata_minuti: 90 })).toBe("1 h 30 min");
  });
});

describe("date della bottega", () => {
  test("il giorno è scritto per esteso, nell'ora di Palermo", () => {
    expect(giorno("2026-11-07T10:00:00+01:00")).toBe("sabato 7 novembre");
    // alle 23:30 UTC a Palermo è già il giorno dopo
    expect(giorno("2026-11-07T23:30:00Z")).toBe("domenica 8 novembre");
  });
  test("l'orario mostra inizio e fine", () => {
    expect(orario("2026-11-07T10:00:00+01:00", "2026-11-07T12:00:00+01:00")).toBe("10:00 – 12:00");
  });
});

describe("postiLiberi", () => {
  test("distingue esaurito, ultimo posto e posti disponibili", () => {
    expect(postiLiberi(0)).toBe("Esaurito");
    expect(postiLiberi(1)).toBe("Ultimo posto!");
    expect(postiLiberi(4)).toBe("4 posti liberi");
  });
});

describe("statoPrenotazione", () => {
  test("traduce gli stati del back-end in parole per il cliente", () => {
    expect(statoPrenotazione("in_attesa")).toBe("Da pagare");
    expect(statoPrenotazione("confermata")).toBe("Confermata");
    expect(statoPrenotazione("annullata")).toBe("Annullata");
  });
});

describe("pannello della titolare", () => {
  test("percentuale arrotondata", () => {
    expect(percentuale(0.756)).toBe("76%");
    expect(percentuale(0)).toBe("0%");
  });
  test("l'ora scelta a Palermo diventa ISO con il fuso giusto, anche con l'ora legale", () => {
    expect(inizioConFuso("2026-11-07", "10:00")).toBe("2026-11-07T10:00:00+01:00");
    expect(inizioConFuso("2027-06-12", "18:30")).toBe("2027-06-12T18:30:00+02:00");
  });
});

describe("euroInCentesimi", () => {
  test("accetta virgola, punto e simbolo dell'euro", () => {
    expect(euroInCentesimi("34")).toBe(3400);
    expect(euroInCentesimi("34,5")).toBe(3450);
    expect(euroInCentesimi("34.50")).toBe(3450);
    expect(euroInCentesimi("0,10 €")).toBe(10); // con i decimali binari 0,10 non sarebbe esatto
  });
  test("rifiuta valori che non sono prezzi", () => {
    expect(euroInCentesimi("-5")).toBeNull();
    expect(euroInCentesimi("dieci")).toBeNull();
    expect(euroInCentesimi("3,456")).toBeNull();
    expect(euroInCentesimi("")).toBeNull();
  });
});

describe("slugDa", () => {
  test("crea un indirizzo leggibile senza accenti né spazi", () => {
    expect(slugDa("Corso di raku all'aperto")).toBe("corso-di-raku-all-aperto");
    expect(slugDa("  Notte in bottega – più ceramica! ")).toBe("notte-in-bottega-piu-ceramica");
  });
});
