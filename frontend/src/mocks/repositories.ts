// MOCK DATA — for UI development only.
// This data is NOT real AI analysis. It will be replaced by backend API responses in Phase 3.

import type { Repository } from '@/types/repository'

export const mockRepositories: Repository[] = [
  {
    id: 'repo-1',
    name: 'todo-api',
    url: 'https://github.com/acme/todo-api',
    description: 'RESTful Todo API built with FastAPI and PostgreSQL',
    defaultBranch: 'main',
    language: 'Python',
    languages: ['Python', 'SQL'],
    status: 'analyzed',
    lastAnalyzedAt: new Date(Date.now() - 2 * 60 * 60 * 1000).toISOString(),
    createdAt: new Date(Date.now() - 7 * 24 * 60 * 60 * 1000).toISOString(),
    updatedAt: new Date(Date.now() - 2 * 60 * 60 * 1000).toISOString(),
    workflowCount: 3,
    lastWorkflowId: 'wf-1',
  },
  {
    id: 'repo-2',
    name: 'auth-service',
    url: 'https://github.com/acme/auth-service',
    description: 'JWT-based authentication microservice',
    defaultBranch: 'main',
    language: 'Python',
    languages: ['Python'],
    status: 'analyzed',
    lastAnalyzedAt: new Date(Date.now() - 24 * 60 * 60 * 1000).toISOString(),
    createdAt: new Date(Date.now() - 14 * 24 * 60 * 60 * 1000).toISOString(),
    updatedAt: new Date(Date.now() - 24 * 60 * 60 * 1000).toISOString(),
    workflowCount: 1,
    lastWorkflowId: 'wf-2',
  },
  {
    id: 'repo-3',
    name: 'data-pipeline',
    url: 'https://github.com/acme/data-pipeline',
    description: 'ETL pipeline for analytics data processing',
    defaultBranch: 'develop',
    language: 'Python',
    languages: ['Python', 'YAML'],
    status: 'idle',
    createdAt: new Date(Date.now() - 3 * 24 * 60 * 60 * 1000).toISOString(),
    updatedAt: new Date(Date.now() - 3 * 24 * 60 * 60 * 1000).toISOString(),
    workflowCount: 0,
  },
]
