import { useEffect } from "react";
import { Route, Routes, useLocation } from "react-router-dom";
import Intestazione from "./components/Intestazione.jsx";
import PiePagina from "./components/PiePagina.jsx";
import Home from "./pages/Home.jsx";
import NonTrovata from "./pages/NonTrovata.jsx";
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
          <Route path="*" element={<NonTrovata />} />
        </Routes>
      </main>
      <PiePagina />
    </>
  );
}
