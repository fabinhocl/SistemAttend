// src/services/api.ts
import axios, { AxiosRequestHeaders } from 'axios'

const api = axios.create({
  baseURL: 'http://127.0.0.1:8000/api/v1',
})

// Interceptor para adicionar token em todas as requisições
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('accessToken')

  if (token) {
    if (!config.headers) {
      config.headers = {} as AxiosRequestHeaders
    }
    (config.headers as any).Authorization = `Bearer ${token}`
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
        localStorage.removeItem('accessToken')
        localStorage.removeItem('refreshToken')
      }
    }
    return Promise.reject(error)
  }
)

export default api
