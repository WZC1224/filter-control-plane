import { defineStore } from 'pinia'
import { computed, ref } from 'vue'
import { loginApi, meApi } from '@/api/auth'
import type { UserRole } from '@/types/api'

export const useUserStore = defineStore(
  'user',
  () => {
    const token = ref('')
    const username = ref('')
    const role = ref<UserRole | ''>('')

    const isAdmin = computed(() => role.value === 'admin')

    async function login(name: string, password: string) {
      const result = await loginApi(name, password)
      token.value = result.token
      username.value = result.username
      role.value = result.role
    }

    async function refreshMe() {
      if (!token.value) return
      const me = await meApi()
      username.value = me.username
      role.value = me.role
    }

    function logout() {
      token.value = ''
      username.value = ''
      role.value = ''
    }

    return { token, username, role, isAdmin, login, refreshMe, logout }
  },
  {
    persist: {
      key: 'fcp-user',
      paths: ['token', 'username', 'role'],
    },
  },
)
