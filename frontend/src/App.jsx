import { Route, Routes } from "react-router-dom";
import Intestazione from "./components/Intestazione.jsx";
import PiePagina from "./components/PiePagina.jsx";
import Home from "./pages/Home.jsx";
import NonTrovata from "./pages/NonTrovata.jsx";

// Mappa delle pagine: ogni indirizzo corrisponde a un componente
export default function App() {
  return (
    <>
      <Intestazione />
      <main>
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="*" element={<NonTrovata />} />
        </Routes>
      </main>
      <PiePagina />
    </>
  );
}
