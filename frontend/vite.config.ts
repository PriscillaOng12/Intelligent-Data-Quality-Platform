import { defineConfig, loadEnv } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig(({ mode }) => {
  // Load environment variables from `.env` files into process.env
  const env = loadEnv(mode, process.cwd(), '');
  return {
    plugins: [react()],
    define: {
      'process.env': env,
    },
    server: {
      port: 5173,
    },
    preview: {
      port: 4173,
    },
  };
});