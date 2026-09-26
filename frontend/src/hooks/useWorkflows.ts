import { useCallback } from 'react'
import { useApiData } from './useApiData'
import { workflowsService } from '@/services/workflows'
import { mockWorkflows } from '@/mocks/workflows'

export function useWorkflows(repositoryId?: string) {
  const fetcher = useCallback(
    () => workflowsService.list(repositoryId),
    [repositoryId]
  )
  return useApiData({
    fetcher,
    mockFallback: mockWorkflows,
  })
}
