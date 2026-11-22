import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'

// Dev server: proxy /api to the Spring Cloud Gateway so the browser stays same-origin.
// In production nginx does the same proxying (see nginx.conf).
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      '/api': {
        target: 'http://localhost:8080',
        changeOrigin: true,
      },
    },
  },
})
