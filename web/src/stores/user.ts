import { defineStore } from 'pinia'
import { ref } from 'vue'
import { loginApi } from '@/api/auth'

export const useUserStore = defineStore(
  'user',
  () => {
    const token = ref('')
    const username = ref('')

    async function login(name: string, password: string) {
      const result = await loginApi(name, password)
      token.value = result.token
      username.value = result.username
    }

    function logout() {
      token.value = ''
      username.value = ''
    }

    return { token, username, login, logout }
  },
  {
    persist: {
      key: 'fcp-user',
      paths: ['token', 'username'],
    },
  },
)
