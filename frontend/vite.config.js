import { defineConfig } from "vite"
import react from "@vitejs/plugin-react"
import process from "node:process"

export default defineConfig({
  plugins: [react()],
  preview: {
    allowedHosts: true,
  },
  server: {
    host: true,          // listen on 0.0.0.0 — makes LAN access possible
    allowedHosts: true,
    proxy: {
      '/api': {
        // 'backend' resolves inside Docker; fall back to localhost for direct dev
        target: process.env.VITE_BACKEND_URL || 'http://localhost:8000',
        changeOrigin: true,
      },
    },
  },
})
