/**
 * useApiData — generic hook for REST resource fetching.
 *
 * Tries the real API first. If the backend is unreachable (network error),
 * falls back to the provided mock data with a clear isMock flag so the UI
 * can show a "mock data" notice.
 *
 * Mock fallback is only used when:
 *   1. The error is a network/connectivity error (backend not running).
 *   2. A mockFallback array is provided by the caller.
 *
 * When the backend returns a 4xx/5xx error, the error is surfaced normally
 * — no mock fallback applies so the developer sees the real problem.
 */

import { useState, useEffect, useCallback } from 'react'

const NETWORK_ERROR_PHRASES = [
  'Unable to reach the backend',
  'Network Error',
  'ERR_CONNECTION_REFUSED',
  'timeout',
]

function isNetworkError(err: unknown): boolean {
  if (!(err instanceof Error)) return false
  return NETWORK_ERROR_PHRASES.some((p) => err.message.includes(p))
}

export interface ApiDataState<T> {
  data: T[]
  loading: boolean
  error: string | null
  /** true when the backend is unreachable and mock data is being shown */
  isMock: boolean
  refetch: () => void
}

interface UseApiDataOptions<T> {
  fetcher: () => Promise<T[]>
  mockFallback?: T[]
  /** Skip the fetch entirely (e.g. when a required param is missing) */
  skip?: boolean
}

export function useApiData<T>({ fetcher, mockFallback, skip }: UseApiDataOptions<T>): ApiDataState<T> {
  const [data, setData] = useState<T[]>([])
  const [loading, setLoading] = useState(!skip)
  const [error, setError] = useState<string | null>(null)
  const [isMock, setIsMock] = useState(false)

  const load = useCallback(async () => {
    if (skip) return
    setLoading(true)
    setError(null)
    setIsMock(false)

    try {
      const result = await fetcher()
      setData(result)
    } catch (err) {
      if (isNetworkError(err) && mockFallback) {
        // Backend not running — show mock data with a clear label
        setData(mockFallback)
        setIsMock(true)
        setError(null)
      } else {
        setError(err instanceof Error ? err.message : 'Failed to load data')
        setData([])
      }
    } finally {
      setLoading(false)
    }
  }, [fetcher, mockFallback, skip])

  useEffect(() => {
    void load()
  }, [load])

  return { data, loading, error, isMock, refetch: load }
}

// ── Single-item variant ──────────────────────────────────────────────────────

export interface ApiItemState<T> {
  data: T | null
  loading: boolean
  error: string | null
  isMock: boolean
  refetch: () => void
}

interface UseApiItemOptions<T> {
  fetcher: () => Promise<T>
  mockFallback?: T
  skip?: boolean
}

export function useApiItem<T>({ fetcher, mockFallback, skip }: UseApiItemOptions<T>): ApiItemState<T> {
  const [data, setData] = useState<T | null>(null)
  const [loading, setLoading] = useState(!skip)
  const [error, setError] = useState<string | null>(null)
  const [isMock, setIsMock] = useState(false)

  const load = useCallback(async () => {
    if (skip) return
    setLoading(true)
    setError(null)
    setIsMock(false)

    try {
      const result = await fetcher()
      setData(result)
    } catch (err) {
      if (isNetworkError(err) && mockFallback !== undefined) {
        setData(mockFallback)
        setIsMock(true)
        setError(null)
      } else {
        setError(err instanceof Error ? err.message : 'Failed to load data')
        setData(null)
      }
    } finally {
      setLoading(false)
    }
  }, [fetcher, mockFallback, skip])

  useEffect(() => {
    void load()
  }, [load])

  return { data, loading, error, isMock, refetch: load }
}
