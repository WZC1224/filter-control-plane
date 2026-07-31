import { createApp } from 'vue'
import { createPinia } from 'pinia'
import piniaPluginPersistedstate from 'pinia-plugin-persistedstate'
import 'element-plus/theme-chalk/dark/css-vars.css'
// 命令式 API（ElMessage / ElMessageBox）不经组件 resolver，须手动拉样式，否则无定位堆在 body 底部
import 'element-plus/es/components/message/style/css'
import 'element-plus/es/components/message-box/style/css'

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
