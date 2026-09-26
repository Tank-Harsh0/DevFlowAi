// NOTE: Backend integration pending.
// Endpoints inferred from docs/ARCHITECTURE.md.

import { apiClient } from './api'
import type { Finding } from '@/types/finding'

export interface FindingsFilter {
  workflowId?: string
  severity?: string
  agent?: string
  status?: string
  file?: string
}

export interface ApprovalPayload {
  approved: true
}

export interface RejectionPayload {
  approved: false
  reason?: string
}

export const findingsService = {
  /** List findings — supports server-side filters when backend implements them */
  list: (filter?: FindingsFilter): Promise<Finding[]> =>
    apiClient
      .get<Finding[]>('/api/v1/findings', { params: filter })
      .then((r) => r.data),

  /** Get a single finding by ID */
  get: (findingId: string): Promise<Finding> =>
    apiClient
      .get<Finding>(`/api/v1/findings/${findingId}`)
      .then((r) => r.data),

  /**
   * Approve a finding's fix proposal.
   * @pending — endpoint path TBC with backend developer.
   * Expected: POST /api/v1/findings/{findingId}/approve
   */
  approveFix: (findingId: string): Promise<Finding> =>
    apiClient
      .post<Finding>(`/api/v1/findings/${findingId}/approve`, {})
      .then((r) => r.data),

  /**
   * Reject a finding's fix proposal.
   * @pending — endpoint path TBC with backend developer.
   * Expected: POST /api/v1/findings/{findingId}/reject
   */
  rejectFix: (findingId: string, reason?: string): Promise<Finding> =>
    apiClient
      .post<Finding>(`/api/v1/findings/${findingId}/reject`, { reason })
      .then((r) => r.data),
}
