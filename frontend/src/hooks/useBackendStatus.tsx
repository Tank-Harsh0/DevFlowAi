import { createContext, useContext, useState, useEffect, useCallback } from 'react'
import { checkBackendHealth } from '@/services/api'

type BackendStatus = 'checking' | 'online' | 'offline'

interface BackendStatusContextValue {
  status: BackendStatus
  recheck: () => void
}

const BackendStatusContext = createContext<BackendStatusContextValue>({
  status: 'checking',
  recheck: () => undefined,
})

export function BackendStatusProvider({ children }: { children: React.ReactNode }) {
  const [status, setStatus] = useState<BackendStatus>('checking')

  const recheck = useCallback(async () => {
    setStatus('checking')
    const ok = await checkBackendHealth()
    setStatus(ok ? 'online' : 'offline')
  }, [])

  // Check on mount and every 30 s
  useEffect(() => {
    void recheck()
    const id = setInterval(() => void recheck(), 30_000)
    return () => clearInterval(id)
  }, [recheck])

  return (
    <BackendStatusContext.Provider value={{ status, recheck }}>
      {children}
    </BackendStatusContext.Provider>
  )
}

// eslint-disable-next-line react-refresh/only-export-components
export function useBackendStatus() {
  return useContext(BackendStatusContext)
}
