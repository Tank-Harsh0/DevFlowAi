import { createContext, useContext, useState, useEffect, useCallback, type ReactNode } from 'react'
import { apiClient } from '@/services/api'
import { authService, type UserProfile } from '@/services/auth'

const TOKEN_KEY = 'devflow_token'

interface AuthContextValue {
  user: UserProfile | null
  token: string | null
  isLoading: boolean
  login: (email: string, password: string) => Promise<void>
  register: (email: string, username: string, password: string) => Promise<void>
  logout: () => void
}

const AuthContext = createContext<AuthContextValue | null>(null)

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<UserProfile | null>(null)
  const [token, setToken] = useState<string | null>(() => localStorage.getItem(TOKEN_KEY))
  const [isLoading, setIsLoading] = useState(true)

  // Inject token into every axios request
  useEffect(() => {
    const id = apiClient.interceptors.request.use((config) => {
      if (token) {
        config.headers.Authorization = `Bearer ${token}`
      }
      return config
    })
    return () => apiClient.interceptors.request.eject(id)
  }, [token])

  // On mount (or when token changes), load the current user
  useEffect(() => {
    if (!token) {
      setUser(null)
      setIsLoading(false)
      return
    }
    authService
      .me()
      .then(setUser)
      .catch(() => {
        // Token invalid or expired — clear it
        localStorage.removeItem(TOKEN_KEY)
        setToken(null)
        setUser(null)
      })
      .finally(() => setIsLoading(false))
  }, [token])

  const _persist = (t: string) => {
    localStorage.setItem(TOKEN_KEY, t)
    setToken(t)
  }

  const login = useCallback(async (email: string, password: string) => {
    const { access_token } = await authService.login(email, password)
    _persist(access_token)
  }, [])

  const register = useCallback(async (email: string, username: string, password: string) => {
    const { access_token } = await authService.register(email, username, password)
    _persist(access_token)
  }, [])

  const logout = useCallback(() => {
    localStorage.removeItem(TOKEN_KEY)
    setToken(null)
    setUser(null)
  }, [])

  return (
    <AuthContext.Provider value={{ user, token, isLoading, login, register, logout }}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error('useAuth must be used inside <AuthProvider>')
  return ctx
}
