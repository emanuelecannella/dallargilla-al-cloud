import { useState } from "react";
import { useAutenticazione } from "../../contesti/Autenticazione.jsx";
import Calendario from "./Calendario.jsx";
import Dashboard from "./Dashboard.jsx";
import Offerta from "./Offerta.jsx";

const SEZIONI = { dashboard: "Andamento", calendario: "Calendario e iscritti", offerta: "Servizi e promozioni" };

// Pannello di amministrazione della titolare (RF15–RF19): andamento, calendario, offerta
export default function Pannello() {
  const { utente } = useAutenticazione();
  const [sezione, setSezione] = useState("dashboard");

  return (
    <section className="contenitore sezione">
      <h1>Pannello della bottega</h1>
      <p>Buon lavoro, {utente.nome}! Qui trovi l'andamento dell'attività, il calendario con gli iscritti e la gestione dell'offerta.</p>
      <nav className="schede" aria-label="Sezioni del pannello">
        {Object.entries(SEZIONI).map(([chiave, nome]) => (
          <button key={chiave} className={sezione === chiave ? "attiva" : ""} onClick={() => setSezione(chiave)}>
            {nome}
          </button>
        ))}
      </nav>
      {sezione === "dashboard" && <Dashboard />}
      {sezione === "calendario" && <Calendario />}
      {sezione === "offerta" && <Offerta />}
    </section>
  );
}
