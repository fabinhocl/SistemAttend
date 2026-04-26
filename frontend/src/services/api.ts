// src/services/api.ts
import axios, { AxiosRequestHeaders } from 'axios'
import { getActiveTenantId } from './tenantSession'

const api = axios.create({
  baseURL: 'http://127.0.0.1:8000/api/v1',
})

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token')
  console.log('TOKEN ENVIADO NO INTERCEPTOR:', token) // Adicione este log

  if (token) {
    config.headers.Authorization = `Bearer ${token}`
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
