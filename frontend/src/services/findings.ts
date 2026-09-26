// NOTE: Backend integration pending.

import { apiClient } from './api'
import type { Finding } from '@/types/finding'

export interface FindingsFilter {
  workflowId?: string
  severity?: string
  agent?: string
  status?: string
  file?: string
}

export const findingsService = {
  list: (filter?: FindingsFilter): Promise<Finding[]> =>
    apiClient
      .get<Finding[]>('/api/v1/findings', { params: filter })
      .then((r) => r.data),

  get: (findingId: string): Promise<Finding> =>
    apiClient
      .get<Finding>(`/api/v1/findings/${findingId}`)
      .then((r) => r.data),
}
