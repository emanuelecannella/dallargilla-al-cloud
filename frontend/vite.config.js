import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// Indirizzo del back-end: in Docker il container si chiama "backend",
// fuori da Docker il server gira su localhost.
const backend = process.env.VITE_API_TARGET || "http://localhost:8000";

export default defineConfig({
  plugins: [react()],
  server: {
    host: true, // raggiungibile anche dall'esterno del container
    port: 5173,
    // Le chiamate a /api passano dal server di sviluppo e vengono girate al back-end:
    // per il browser front-end e API hanno la stessa origine.
    proxy: { "/api": backend },
    // Dentro Docker su Mac le modifiche ai file si rilevano in modo affidabile solo con il polling
    watch: { usePolling: process.env.VITE_POLLING === "true" },
  },
  test: { environment: "node" },
});
