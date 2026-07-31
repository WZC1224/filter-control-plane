import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import AutoImport from 'unplugin-auto-import/vite'
import Components from 'unplugin-vue-components/vite'
import { ElementPlusResolver } from 'unplugin-vue-components/resolvers'
import { fileURLToPath, URL } from 'node:url'
import type { ProxyOptions } from 'vite'

/** SPA 路由与 API 前缀撞名（/orders /tasks …）：浏览器刷新带 Accept:text/html，勿代理到 Flask。 */
function apiProxy(target = 'http://127.0.0.1:5100'): ProxyOptions {
  return {
    target,
    changeOrigin: true,
    bypass(req) {
      const accept = req.headers.accept || ''
      if (accept.includes('text/html')) {
        return '/index.html'
      }
    },
  }
}

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
      '/auth': apiProxy(),
      '/tasks': apiProxy(),
      '/meta': apiProxy(),
      '/orders': apiProxy(),
      '/bills': apiProxy(),
      '/notices': apiProxy(),
      '/users': apiProxy(),
    },
  },
  build: {
    outDir: 'dist',
    emptyOutDir: true,
  },
})
