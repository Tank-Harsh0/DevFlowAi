import { useCallback } from 'react'
import { useApiData } from './useApiData'
import { repositoriesService } from '@/services/repositories'
import { mockRepositories } from '@/mocks/repositories'

export function useRepositories() {
  const fetcher = useCallback(() => repositoriesService.list(), [])
  return useApiData({
    fetcher,
    mockFallback: mockRepositories,
  })
}
