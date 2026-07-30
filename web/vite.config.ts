import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import AutoImport from 'unplugin-auto-import/vite'
import Components from 'unplugin-vue-components/vite'
import { ElementPlusResolver } from 'unplugin-vue-components/resolvers'
import { fileURLToPath, URL } from 'node:url'

export default defineConfig({
  plugins: [
    vue(),
    AutoImport({
      resolvers: [ElementPlusResolver()],
      dts: 'src/auto-imports.d.ts',
    }),
    Components({
      resolvers: [ElementPlusResolver()],
      dts: 'src/components.d.ts',
    }),
  ],
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
      '/users': { target: 'http://127.0.0.1:5100', changeOrigin: true },
    },
  },
  build: {
    outDir: 'dist',
    emptyOutDir: true,
  },
})
