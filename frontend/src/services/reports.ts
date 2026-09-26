// NOTE: Backend integration pending.

import { apiClient } from './api'
import type { Report } from '@/types/report'

export const reportsService = {
  get: (workflowId: string): Promise<Report> =>
    apiClient
      .get<Report>(`/api/v1/workflows/${workflowId}/report`)
      .then((r) => r.data),

  list: (): Promise<Report[]> =>
    apiClient
      .get<Report[]>('/api/v1/reports')
      .then((r) => r.data),
}
