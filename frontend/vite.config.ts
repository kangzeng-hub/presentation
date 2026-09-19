import {defineConfig} from 'vite';
import react from '@vitejs/plugin-react';

// The workspace UI uses FastAPI as the sole formal business backend.
export default defineConfig({
  plugins: [react()],
  server: {
    host: '0.0.0.0',
    proxy: {
      // Keep React workspace routes (/projects/...) out of the API proxy.
      // The typed client calls FastAPI directly; only portfolio data uses /api.
      '/api': 'http://127.0.0.1:8000',
    },
  },
});
