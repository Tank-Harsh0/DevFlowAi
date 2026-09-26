import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    // Bind to all interfaces so the dev server is reachable inside Docker.
    // 'true' uses 0.0.0.0 which exposes to all network interfaces.
    host: true,
    port: 5173,
  },
  preview: {
    host: true,
    port: 5173,
  },
})
