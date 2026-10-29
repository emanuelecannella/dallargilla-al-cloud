import { Navigate, useLocation } from "react-router-dom";
import { useAutenticazione } from "../contesti/Autenticazione.jsx";

/** Mostra la pagina solo a chi ha fatto l'accesso (e, se richiesto, solo alla titolare). */
export default function RottaProtetta({ children, soloAdmin = false }) {
  const { utente, verifica } = useAutenticazione();
  const posizione = useLocation();
  if (verifica) return <p className="contenitore sezione">Verifica dell'accesso…</p>;
  if (!utente) return <Navigate to={`/accesso?da=${encodeURIComponent(posizione.pathname)}`} replace />;
  // La protezione vera è sul server; qui evitiamo solo di mostrare una pagina che non funzionerebbe
  if (soloAdmin && utente.ruolo !== "admin") return <Navigate to="/area-personale" replace />;
  return children;
}
