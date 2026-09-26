import { useCallback } from 'react'
import { useApiData } from './useApiData'
import { reportsService } from '@/services/reports'
import { mockReports } from '@/mocks/reports'

export function useReports() {
  const fetcher = useCallback(() => reportsService.list(), [])
  return useApiData({
    fetcher,
    mockFallback: mockReports,
  })
}
