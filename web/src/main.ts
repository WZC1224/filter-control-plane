import { createApp } from 'vue'
import { createPinia } from 'pinia'
import piniaPluginPersistedstate from 'pinia-plugin-persistedstate'
import 'element-plus/theme-chalk/dark/css-vars.css'

import App from './App.vue'
import router from './router'
import { applyThemeFromStorage, useThemeStore } from '@/stores/theme'
import './styles/index.scss'

applyThemeFromStorage()

const app = createApp(App)
const pinia = createPinia()
pinia.use(piniaPluginPersistedstate)

app.use(pinia)
useThemeStore().syncFromStore()
app.use(router)
app.mount('#app')
