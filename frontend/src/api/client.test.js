import { describe, expect, test } from "vitest";
import { messaggioErrore } from "./client.js";

describe("messaggioErrore", () => {
  test("usa il messaggio delle regole della bottega", () => {
    expect(messaggioErrore({ detail: "Posti esauriti per questa data", codice: "POSTI_ESAURITI" }))
      .toBe("Posti esauriti per questa data");
  });
  test("traduce un errore di validazione nel suo messaggio, senza il prefisso tecnico", () => {
    const dati = { detail: [{ loc: ["body", "telefono"], msg: "Value error, Il numero di telefono non è valido" }] };
    expect(messaggioErrore(dati)).toBe("Il numero di telefono non è valido");
  });
  test("ha un messaggio di riserva", () => {
    expect(messaggioErrore(null)).toBe("Si è verificato un errore.");
  });
});
