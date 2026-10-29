import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { BrowserRouter } from "react-router-dom";
import App from "./App.jsx";
import { FornitoreAutenticazione } from "./contesti/Autenticazione.jsx";
import "./stili.css";

createRoot(document.getElementById("root")).render(
  <StrictMode>
    <BrowserRouter>
      <FornitoreAutenticazione>
        <App />
      </FornitoreAutenticazione>
    </BrowserRouter>
  </StrictMode>,
);
