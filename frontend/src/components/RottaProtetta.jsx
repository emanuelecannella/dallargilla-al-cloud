import { Navigate, useLocation } from "react-router-dom";
import { useAutenticazione } from "../contesti/Autenticazione.jsx";

/** Mostra la pagina solo a chi ha fatto l'accesso; gli altri vengono mandati alla pagina di accesso. */
export default function RottaProtetta({ children }) {
  const { utente, verifica } = useAutenticazione();
  const posizione = useLocation();
  if (verifica) return <p className="contenitore sezione">Verifica dell'accesso…</p>;
  if (!utente) return <Navigate to={`/accesso?da=${encodeURIComponent(posizione.pathname)}`} replace />;
  return children;
}
