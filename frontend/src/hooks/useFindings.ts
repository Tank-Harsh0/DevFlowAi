import { useCallback, useEffect, useRef } from 'react'
import { useApiData } from './useApiData'
import { findingsService, type FindingsFilter } from '@/services/findings'
import { mockFindings } from '@/mocks/findings'

export function useFindings(filter?: FindingsFilter) {
  // Serialize the filter so we can safely use it as a useEffect dependency
  // without triggering on every render due to object identity changes.
  const filterKey = JSON.stringify(filter ?? null)
  const filterRef = useRef<FindingsFilter | undefined>(filter)

  // Update filterRef inside an effect to satisfy react-hooks/refs
  useEffect(() => {
    filterRef.current = filter
  }, [filter])

  const fetcher = useCallback(
    () => findingsService.list(filterRef.current),
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [filterKey]
  )

  return useApiData({
    fetcher,
    mockFallback: mockFindings,
  })
}
