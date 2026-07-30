import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import { fileURLToPath, URL } from 'node:url'

export default defineConfig({
  plugins: [vue()],
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url)),
    },
  },
  server: {
    port: 5173,
    proxy: {
      '/auth': { target: 'http://127.0.0.1:5100', changeOrigin: true },
      '/tasks': { target: 'http://127.0.0.1:5100', changeOrigin: true },
      '/meta': { target: 'http://127.0.0.1:5100', changeOrigin: true },
      '/orders': { target: 'http://127.0.0.1:5100', changeOrigin: true },
      '/bills': { target: 'http://127.0.0.1:5100', changeOrigin: true },
      '/notices': { target: 'http://127.0.0.1:5100', changeOrigin: true },
    },
  },
  build: {
    outDir: 'dist',
    emptyOutDir: true,
  },
})
