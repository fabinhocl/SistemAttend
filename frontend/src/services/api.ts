// src/services/api.ts
import axios, { AxiosRequestHeaders } from 'axios'
import { getActiveTenantId } from './tenantSession'

const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000/api',
})

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token')
  const tenantId = getActiveTenantId()

  if (config.headers == null) {
    config.headers = {} as any
  }

  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }

  if (tenantId) {
    config.headers['X-Tenant-Id'] = tenantId
  }

  return config
})

// interceptor de resposta: limpa token se vier 401
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      // só limpa se não for rota de login/registro
      const url = error.config?.url || ''
      if (!url.includes('token') && !url.includes('registro')) {
        localStorage.removeItem('access_token')
        localStorage.removeItem('refreshToken')
      }
    }
    return Promise.reject(error)
  }
)

export default api
