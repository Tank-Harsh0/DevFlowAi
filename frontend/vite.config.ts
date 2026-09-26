import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'
import { defineConfig } from 'vite'

// https://vite.dev/config/
export default defineConfig({
<<<<<<< HEAD
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
=======
  plugins: [react(), tailwindcss()],
  resolve: {
    alias: {
      '@': `${import.meta.dirname}/src`,
    },
>>>>>>> f64b0c4c97422ec52ec9706f2a4809f7662c29b0
  },
})
