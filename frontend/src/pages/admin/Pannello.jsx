import { useState } from "react";
import { useAutenticazione } from "../../contesti/Autenticazione.jsx";
import Calendario from "./Calendario.jsx";
import Dashboard from "./Dashboard.jsx";

const SEZIONI = { dashboard: "Andamento", calendario: "Calendario e iscritti" };

// Pannello di amministrazione della titolare (RF15–RF19)
export default function Pannello() {
  const { utente } = useAutenticazione();
  const [sezione, setSezione] = useState("dashboard");

  return (
    <section className="contenitore sezione">
      <h1>Pannello della bottega</h1>
      <p>Buon lavoro, {utente.nome}! Qui trovi l'andamento dell'attività e il calendario con gli iscritti.</p>
      <nav className="schede" aria-label="Sezioni del pannello">
        {Object.entries(SEZIONI).map(([chiave, nome]) => (
          <button key={chiave} className={sezione === chiave ? "attiva" : ""} onClick={() => setSezione(chiave)}>
            {nome}
          </button>
        ))}
      </nav>
      {sezione === "dashboard" ? <Dashboard /> : <Calendario />}
    </section>
  );
}
