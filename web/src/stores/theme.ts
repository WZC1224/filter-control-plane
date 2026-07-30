import { defineStore } from 'pinia'
import { computed, ref, watch } from 'vue'

export type ThemeMode = 'light' | 'dark'

export function applyDom(mode: ThemeMode) {
  const root = document.documentElement
  root.classList.toggle('dark', mode === 'dark')
  root.dataset.theme = mode
}

/** 启动前读 localStorage，避免先闪白天 */
export function applyThemeFromStorage() {
  try {
    const raw = localStorage.getItem('fcp-theme')
    if (!raw) return
    const parsed = JSON.parse(raw) as { mode?: ThemeMode }
    if (parsed?.mode === 'dark' || parsed?.mode === 'light') {
      applyDom(parsed.mode)
    }
  } catch {
    // ignore
  }
}

export const useThemeStore = defineStore(
  'theme',
  () => {
    const mode = ref<ThemeMode>('light')
    const isDark = computed(() => mode.value === 'dark')

    function setMode(next: ThemeMode) {
      mode.value = next
      applyDom(next)
    }

    function toggle() {
      setMode(mode.value === 'dark' ? 'light' : 'dark')
    }

    function syncFromStore() {
      applyDom(mode.value)
    }

    watch(mode, (v) => applyDom(v))

    return { mode, isDark, setMode, toggle, syncFromStore }
  },
  {
    persist: {
      key: 'fcp-theme',
      paths: ['mode'],
      afterRestore: (ctx) => {
        applyDom(ctx.store.mode as ThemeMode)
      },
    },
  },
)
