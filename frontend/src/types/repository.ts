// NOTE: These types are pending backend API confirmation.

export type RepositoryStatus = 'idle' | 'analyzing' | 'analyzed' | 'error'

export interface Repository {
  id: string
  name: string
  url: string
  description?: string
  defaultBranch?: string
  language?: string
  languages?: string[]
  status: RepositoryStatus
  lastAnalyzedAt?: string
  createdAt: string
  updatedAt: string
  workflowCount?: number
  lastWorkflowId?: string
}

export interface AddRepositoryRequest {
  url: string
  name?: string
  defaultBranch?: string
}
