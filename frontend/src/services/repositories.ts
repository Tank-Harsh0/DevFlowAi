// NOTE: Backend integration pending.

import { apiClient } from './api'
import type { Repository, AddRepositoryRequest } from '@/types/repository'

export const repositoriesService = {
  list: (): Promise<Repository[]> =>
    apiClient
      .get<Repository[]>('/api/v1/repositories')
      .then((r) => r.data),

  get: (repositoryId: string): Promise<Repository> =>
    apiClient
      .get<Repository>(`/api/v1/repositories/${repositoryId}`)
      .then((r) => r.data),

  add: (data: AddRepositoryRequest): Promise<Repository> =>
    apiClient
      .post<Repository>('/api/v1/repositories', data)
      .then((r) => r.data),

  remove: (repositoryId: string): Promise<void> =>
    apiClient
      .delete(`/api/v1/repositories/${repositoryId}`)
      .then(() => undefined),
}
