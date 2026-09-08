import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    host: true,
    allowedHosts: [
      'jnsiq-2401-4900-1c54-cca8-44ed-df9e-1a2-6e65.free.pinggy.net',
      'lwxiz-2401-4900-1c54-cca8-44ed-df9e-1a2-6e65.run.pinggy-free.link'
    ],
    port: 3000,
    proxy: {
      '/api': {
        target: 'http://127.0.0.1:8001',
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api/, ''),
      },
    },
  },
})
