import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import tailwindcss from "@tailwindcss/vite";

export default defineConfig({
  plugins: [react(), tailwindcss()],
  // the API runs on its own port; the browser only talks to Vite
  // changeOrigin: the API only accepts Host 127.0.0.1, and a phone sends the Mac's Wi-Fi address (./run.sh phone)
  server: { host: "127.0.0.1", port: 5173, proxy: { "/api": { target: "http://127.0.0.1:8000", changeOrigin: true } } },
});
