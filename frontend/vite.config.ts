import {defineConfig} from 'vite';
import react from '@vitejs/plugin-react';

// The workspace UI talks to the stateful demo backend on :4010 in both dev
// and Compose. Keep the proxy explicit for local browser sessions that use
// relative URLs, and avoid silently routing workspace calls to the unrelated
// calibration API on :8000.
export default defineConfig({
  plugins: [react()],
  server: {
    host: '0.0.0.0',
    proxy: {
      '/projects': 'http://localhost:4010',
      '/health': 'http://localhost:4010',
    },
  },
});
