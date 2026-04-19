import { ref } from 'vue'
import { useRouter } from 'vue-router'
import api from '../services/api'

const token = ref(localStorage.getItem('access_token') || '')
const user = ref(null)

export const useAuth = () => {
  const router = useRouter()

  const login = async (username: string, password: string) => {
    try {
      const response = await api.post('/token/', {
        username,
        password
      })

      token.value = response.data.access
      localStorage.setItem('access_token', response.data.access)
      localStorage.setItem('refresh_token', response.data.refresh)

      // Setar header padrão para próximas requisições
      api.defaults.headers.common['Authorization'] = `Bearer ${token.value}`

      return true
    } catch (error: any) {
      throw new Error(error.response?.data?.detail || 'Erro ao fazer login')
    }
  }

  const logout = () => {
    token.value = ''
    user.value = null
    localStorage.removeItem('access_token')
    localStorage.removeItem('refresh_token')
    delete api.defaults.headers.common['Authorization']
    router.push('/login')
  }

  const isAuthenticated = () => !!token.value

  return {
    token,
    user,
    login,
    logout,
    isAuthenticated
  }
}
