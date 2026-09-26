import axios from 'axios'

const BASE_URL = import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000'

export const apiClient = axios.create({
  baseURL: BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 30_000,
})

// Request interceptor — attach auth headers when available
apiClient.interceptors.request.use((config) => {
  return config
})

// Response interceptor — normalize errors
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    const message: string =
      (error.response?.data as { detail?: string })?.detail ??
      error.message ??
      'An unknown error occurred'
    return Promise.reject(new Error(message))
  }
)

export const WEBSOCKET_URL = import.meta.env.VITE_WS_URL ?? 'ws://localhost:8000'
