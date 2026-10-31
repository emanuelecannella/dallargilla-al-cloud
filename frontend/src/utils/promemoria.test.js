// Test della funzione promemoria (Emanuele Francesco Cannella)
import { describe, expect, test } from "vitest";
import { promemoria } from "./promemoria.js";

// Fingiamo che oggi sia venerdì 6 novembre 2026, alle 18 a Palermo
const venerdi = new Date("2026-11-06T18:00:00+01:00");

describe("promemoria", () => {
  test("lezione oggi, domani o tra qualche giorno", () => {
    expect(promemoria("2026-11-06T20:00:00+01:00", venerdi)).toBe("Oggi!");
    expect(promemoria("2026-11-07T10:00:00+01:00", venerdi)).toBe("Domani");
    expect(promemoria("2026-11-12T10:00:00+01:00", venerdi)).toBe("Tra 6 giorni");
  });

  test("una lezione già passata non ha promemoria", () => {
    expect(promemoria("2026-11-05T10:00:00+01:00", venerdi)).toBe("");
  });

  test("conta i giorni di calendario, non le ore", () => {
    // alle 23:30, una lezione a mezzanotte e mezza è tra un'ora, ma è "domani"
    const tardi = new Date("2026-11-06T23:30:00+01:00");
    expect(promemoria("2026-11-07T00:30:00+01:00", tardi)).toBe("Domani");
  });

  test("funziona anche con il cambio dell'ora legale", () => {
    // il 25 ottobre 2026 le lancette tornano indietro di un'ora
    const sabato = new Date("2026-10-24T10:00:00+02:00");
    expect(promemoria("2026-10-26T10:00:00+01:00", sabato)).toBe("Tra 2 giorni");
  });
});