import { defineStore } from 'pinia'
import { ref } from 'vue'
import { authApi } from '../api/mcp'

export const useAuthStore = defineStore('auth', () => {
  const authEnabled = ref(false)
  const initialized = ref(false)
  const apiKey = ref('')
  const token = ref(localStorage.getItem('token') || '')
  const username = ref(localStorage.getItem('username') || '')
  const loaded = ref(false)

  const isLoggedIn = () => !authEnabled.value || !!token.value

  async function fetchAuthStatus() {
    const res = await authApi.status()
    authEnabled.value = res.data.enabled
    initialized.value = res.data.initialized
    apiKey.value = res.data.api_key || ''
    loaded.value = true
  }

  function setAuth(t: string, u: string) {
    token.value = t
    username.value = u
    localStorage.setItem('token', t)
    localStorage.setItem('username', u)
  }

  function logout() {
    token.value = ''
    username.value = ''
    localStorage.removeItem('token')
    localStorage.removeItem('username')
  }

  return { authEnabled, initialized, apiKey, token, username, loaded, isLoggedIn, fetchAuthStatus, setAuth, logout }
})
