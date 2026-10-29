import { createContext, useCallback, useContext, useEffect, useMemo, useState } from "react";
import { account } from "../api/client.js";

// Il token di accesso viene ricordato nel browser, così ricaricando la pagina si resta collegati.
// Scade comunque dopo 60 minuti: a quel punto il server lo rifiuta e si torna a chiedere l'accesso.
const CHIAVE = "terracotta-viva-token";

function leggiToken() {
  try {
    return localStorage.getItem(CHIAVE);
  } catch {
    return null; // navigazione privata o archiviazione bloccata
  }
}

function salvaToken(token) {
  try {
    if (token) localStorage.setItem(CHIAVE, token);
    else localStorage.removeItem(CHIAVE);
  } catch {
    /* il token resta solo in memoria */
  }
}

const ContestoAutenticazione = createContext(null);

/** Fornisce a tutta l'applicazione l'utente collegato e le azioni di accesso e uscita. */
export function FornitoreAutenticazione({ children }) {
  const [token, setToken] = useState(leggiToken);
  const [utente, setUtente] = useState(null);
  const [verifica, setVerifica] = useState(Boolean(leggiToken()));

  const esci = useCallback(() => {
    salvaToken(null);
    setToken(null);
    setUtente(null);
  }, []);

  // Se una chiamata scopre che l'accesso è scaduto, si esce: le pagine protette chiederanno di rientrare
  useEffect(() => {
    window.addEventListener("sessione-scaduta", esci);
    return () => window.removeEventListener("sessione-scaduta", esci);
  }, [esci]);

  // Con un token salvato, chiediamo al server chi siamo: se è scaduto, si esce
  useEffect(() => {
    if (!token) {
      setVerifica(false);
      return;
    }
    let attivo = true;
    account
      .profilo(token)
      .then((dati) => attivo && setUtente(dati))
      // Si esce solo se il server rifiuta il token (401); un problema di rete o una pagina
      // ricaricata a metà non devono far perdere l'accesso
      .catch((e) => attivo && e.stato === 401 && esci())
      .finally(() => attivo && setVerifica(false));
    return () => {
      attivo = false;
    };
  }, [token, esci]);

  const accedi = useCallback(async (email, password) => {
    const { access_token } = await account.login(email, password);
    const profilo = await account.profilo(access_token);
    salvaToken(access_token);
    setToken(access_token);
    setUtente(profilo);
    return profilo;
  }, []);

  const aggiornaProfilo = useCallback(
    async (dati) => {
      const profilo = await account.aggiornaProfilo(token, dati);
      setUtente(profilo);
      return profilo;
    },
    [token],
  );

  const valore = useMemo(
    () => ({ token, utente, verifica, accedi, esci, aggiornaProfilo }),
    [token, utente, verifica, accedi, esci, aggiornaProfilo],
  );
  return <ContestoAutenticazione.Provider value={valore}>{children}</ContestoAutenticazione.Provider>;
}

export function useAutenticazione() {
  return useContext(ContestoAutenticazione);
}
