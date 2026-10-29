import { useEffect } from "react";
import { Route, Routes, useLocation } from "react-router-dom";
import Intestazione from "./components/Intestazione.jsx";
import RottaProtetta from "./components/RottaProtetta.jsx";
import PiePagina from "./components/PiePagina.jsx";
import Accesso from "./pages/Accesso.jsx";
import AreaPersonale from "./pages/AreaPersonale.jsx";
import Home from "./pages/Home.jsx";
import NonTrovata from "./pages/NonTrovata.jsx";
import Registrazione from "./pages/Registrazione.jsx";
import Servizio from "./pages/Servizio.jsx";

// Ogni cambio di pagina riparte dall'alto; con un'ancora (#servizi) scorre fino alla sezione
function ScorriInAlto() {
  const { pathname, hash } = useLocation();
  useEffect(() => {
    const destinazione = hash && document.getElementById(hash.slice(1));
    if (destinazione) destinazione.scrollIntoView();
    else window.scrollTo(0, 0);
  }, [pathname, hash]);
  return null;
}

// Mappa delle pagine: ogni indirizzo corrisponde a un componente
export default function App() {
  return (
    <>
      <ScorriInAlto />
      <Intestazione />
      <main>
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/servizi/:slug" element={<Servizio />} />
          <Route path="/accesso" element={<Accesso />} />
          <Route path="/registrazione" element={<Registrazione />} />
          <Route
            path="/area-personale"
            element={<RottaProtetta><AreaPersonale /></RottaProtetta>}
          />
          <Route path="*" element={<NonTrovata />} />
        </Routes>
      </main>
      <PiePagina />
    </>
  );
}
