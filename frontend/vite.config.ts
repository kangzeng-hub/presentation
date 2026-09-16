import {defineConfig} from 'vite';
import react from '@vitejs/plugin-react';

// The workspace UI uses FastAPI as the sole formal business backend.
export default defineConfig({
  plugins: [react()],
  server: {
    host: '0.0.0.0',
    proxy: {
      '/projects': 'http://localhost:8000',
      '/jobs': 'http://localhost:8000',
      '/health': 'http://localhost:8000',
    },
  },
});
