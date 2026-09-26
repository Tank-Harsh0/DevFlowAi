import { useCallback } from 'react'
import { useApiItem } from './useApiData'
import { findingsService } from '@/services/findings'
import { mockFindings } from '@/mocks/findings'
import type { Finding } from '@/types/finding'

/**
 * Fetches a single finding by ID.
 * Falls back to the matching mock finding when the backend is unreachable.
 */
export function useFinding(findingId: string | null) {
  const mockFallback: Finding | undefined = findingId
    ? mockFindings.find((f) => f.id === findingId)
    : undefined

  const fetcher = useCallback(
    () => {
      if (!findingId) return Promise.reject(new Error('No finding ID'))
      return findingsService.get(findingId)
    },
    [findingId]
  )

  return useApiItem<Finding>({
    fetcher,
    mockFallback,
    skip: !findingId,
  })
}
