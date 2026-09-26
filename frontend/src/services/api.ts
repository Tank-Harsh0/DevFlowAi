import axios, { type AxiosError } from 'axios'

const BASE_URL = import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000'

export const apiClient = axios.create({
  baseURL: BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 15_000,
})

// Request interceptor — attach auth headers when available
apiClient.interceptors.request.use((config) => {
  return config
})

// Response interceptor — normalize errors into human-readable messages
apiClient.interceptors.response.use(
  (response) => response,
  (error: AxiosError) => {
    let message = 'An unknown error occurred'

    if (error.code === 'ECONNABORTED' || error.message?.includes('timeout')) {
      message = 'Request timed out. The backend may be overloaded or unreachable.'
    } else if (!error.response) {
      // Network error — backend not reachable
      message = 'Unable to reach the backend. Make sure the API server is running.'
    } else {
      const status = error.response.status
      const detail = (error.response.data as { detail?: string } | undefined)?.detail

      if (detail) {
        message = detail
      } else if (status === 400) {
        message = 'Invalid request. Please check the input and try again.'
      } else if (status === 401) {
        message = 'Unauthorized. Please check your credentials.'
      } else if (status === 403) {
        message = 'You do not have permission to perform this action.'
      } else if (status === 404) {
        message = 'The requested resource was not found.'
      } else if (status === 409) {
        message = 'A conflict occurred. The resource may already exist.'
      } else if (status === 422) {
        message = 'Validation error. The request data is invalid.'
      } else if (status === 429) {
        message = 'Too many requests. Please slow down and try again.'
      } else if (status >= 500) {
        message = 'The server encountered an error. Please try again later.'
      }
    }

    return Promise.reject(new Error(message))
  }
)

export const WEBSOCKET_URL =
  import.meta.env.VITE_WS_URL ??
  BASE_URL.replace(/^http/, 'ws')

/**
 * Check whether the backend is reachable.
 * Hits GET /health — if the endpoint doesn't exist a 404 is still a "reachable" backend.
 * Returns false only on network/timeout errors.
 */
export async function checkBackendHealth(): Promise<boolean> {
  try {
    await apiClient.get('/health', { timeout: 4_000 })
    return true
  } catch (err) {
    // 4xx/5xx responses still mean the backend is up — only network errors mean it's down
    if (err instanceof Error) {
      const isNetworkError =
        err.message.includes('Unable to reach') ||
        err.message.includes('timeout')
      return !isNetworkError
    }
    return false
  }
}
