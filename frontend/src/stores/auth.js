import { reactive } from 'vue'
import { api } from '../api'

const TOKEN_KEY = 'netops_token'
const saved = localStorage.getItem(TOKEN_KEY)

export const auth = reactive({
  token: saved || null,
  user: null,
  loading: false,

  get isAuthenticated() {
    return !!this.token
  },

  async login(username, password) {
    this.loading = true
    try {
      const { data } = await api.post('/auth/login', { username, password })
      this.token = data.access_token
      this.user = { username: data.username, role: data.role }
      localStorage.setItem(TOKEN_KEY, data.access_token)
      // Set default header
      api.defaults.headers.common['Authorization'] = `Bearer ${data.access_token}`
      return data
    } finally {
      this.loading = false
    }
  },

  async loadUser() {
    if (!this.token) return
    try {
      api.defaults.headers.common['Authorization'] = `Bearer ${this.token}`
      const { data } = await api.get('/auth/me')
      this.user = { username: data.username, role: data.role }
    } catch {
      this.logout()
    }
  },

  logout() {
    this.token = null
    this.user = null
    localStorage.removeItem(TOKEN_KEY)
    delete api.defaults.headers.common['Authorization']
  },
})
