import { defineConfig } from 'vite';

export default defineConfig({
  root: 'backend/templates',
  build: {
    outDir: '../../dist',
    emptyOutDir: true,
    rollupOptions: {
      input: 'backend/templates/index.html'
    }
  }
});
