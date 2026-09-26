import { apiClient } from './api'
import type { WorkflowRun } from '@/types/workflow'

export const workflowsService = {
  /** List all workflow runs, optionally filtered by repository */
  list: (repositoryId?: string): Promise<WorkflowRun[]> =>
    apiClient
      .get<WorkflowRun[]>('/api/v1/workflows', { params: { repositoryId } })
      .then((r) => r.data),

  /** Get a single workflow run by ID */
  get: (workflowId: string): Promise<WorkflowRun> =>
    apiClient
      .get<WorkflowRun>(`/api/v1/workflows/${workflowId}`)
      .then((r) => r.data),

  /** Start a new workflow run for the given repository */
  start: (repositoryId: string): Promise<WorkflowRun> =>
    apiClient
      .post<WorkflowRun>('/api/v1/workflows', { repositoryId })
      .then((r) => r.data),

  /** Submit an approval decision for a human-approval step */
  submitApproval: (
    workflowId: string,
    stepId: string,
    approved: boolean,
    note?: string
  ): Promise<void> =>
    apiClient
      .post(`/api/v1/workflows/${workflowId}/steps/${stepId}/approval`, {
        approved,
        note,
      })
      .then(() => undefined),
}
