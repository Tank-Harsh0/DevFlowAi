// MOCK DATA — for UI development only.
// This data is NOT real AI analysis. It will be replaced by backend API responses in Phase 3.

import type { WorkflowRun } from '@/types/workflow'

export const mockWorkflows: WorkflowRun[] = [
  {
    id: 'wf-1',
    repositoryId: 'repo-1',
    repositoryName: 'todo-api',
    status: 'completed',
    createdAt: new Date(Date.now() - 2 * 60 * 60 * 1000).toISOString(),
    updatedAt: new Date(Date.now() - 90 * 60 * 1000).toISOString(),
    completedAt: new Date(Date.now() - 90 * 60 * 1000).toISOString(),
    totalFindings: 6,
    fixedFindings: 2,
    testsGenerated: 7,
    testsPassed: 25,
    steps: [
      { id: 's1', name: 'repository_analyzer', label: 'Repository Analysis', status: 'completed', progress: 100, startedAt: new Date(Date.now() - 2 * 60 * 60 * 1000).toISOString(), completedAt: new Date(Date.now() - 118 * 60 * 1000).toISOString(), message: 'Repository structure analyzed — 47 files, 2,341 lines' },
      { id: 's2', name: 'orchestrator', label: 'Orchestrator', status: 'completed', progress: 100, startedAt: new Date(Date.now() - 118 * 60 * 1000).toISOString(), completedAt: new Date(Date.now() - 116 * 60 * 1000).toISOString(), message: 'Analysis plan created' },
      { id: 's3', name: 'code_review', label: 'Code Review', status: 'completed', progress: 100, findingsCount: 2, startedAt: new Date(Date.now() - 116 * 60 * 1000).toISOString(), completedAt: new Date(Date.now() - 110 * 60 * 1000).toISOString(), message: '2 issues discovered' },
      { id: 's4', name: 'security', label: 'Security Analysis', status: 'completed', progress: 100, findingsCount: 2, startedAt: new Date(Date.now() - 116 * 60 * 1000).toISOString(), completedAt: new Date(Date.now() - 108 * 60 * 1000).toISOString(), message: '2 issues discovered' },
      { id: 's5', name: 'test_analysis', label: 'Test Analysis', status: 'completed', progress: 100, findingsCount: 1, startedAt: new Date(Date.now() - 116 * 60 * 1000).toISOString(), completedAt: new Date(Date.now() - 111 * 60 * 1000).toISOString(), message: '1 issue discovered' },
      { id: 's6', name: 'documentation', label: 'Documentation', status: 'completed', progress: 100, findingsCount: 1, startedAt: new Date(Date.now() - 116 * 60 * 1000).toISOString(), completedAt: new Date(Date.now() - 112 * 60 * 1000).toISOString(), message: '1 issue discovered' },
      { id: 's7', name: 'finding_aggregation', label: 'Finding Aggregation', status: 'completed', progress: 100, startedAt: new Date(Date.now() - 107 * 60 * 1000).toISOString(), completedAt: new Date(Date.now() - 106 * 60 * 1000).toISOString(), message: '6 total findings aggregated' },
      { id: 's8', name: 'fix_planning', label: 'Fix Planning', status: 'completed', progress: 100, startedAt: new Date(Date.now() - 106 * 60 * 1000).toISOString(), completedAt: new Date(Date.now() - 104 * 60 * 1000).toISOString(), message: '3 fix proposals generated' },
      { id: 's9', name: 'human_approval', label: 'Human Approval', status: 'completed', progress: 100, startedAt: new Date(Date.now() - 104 * 60 * 1000).toISOString(), completedAt: new Date(Date.now() - 100 * 60 * 1000).toISOString(), message: '2 fixes approved, 1 rejected' },
      { id: 's10', name: 'testing', label: 'Testing', status: 'completed', progress: 100, startedAt: new Date(Date.now() - 100 * 60 * 1000).toISOString(), completedAt: new Date(Date.now() - 95 * 60 * 1000).toISOString(), message: '7 tests generated, 25/25 passed' },
      { id: 's11', name: 'verification', label: 'Verification', status: 'completed', progress: 100, startedAt: new Date(Date.now() - 95 * 60 * 1000).toISOString(), completedAt: new Date(Date.now() - 93 * 60 * 1000).toISOString(), message: 'All checks passed' },
      { id: 's12', name: 'final_report', label: 'Final Report', status: 'completed', progress: 100, startedAt: new Date(Date.now() - 93 * 60 * 1000).toISOString(), completedAt: new Date(Date.now() - 90 * 60 * 1000).toISOString(), message: 'Report generated' },
    ],
  },
  {
    id: 'wf-2',
    repositoryId: 'repo-2',
    repositoryName: 'auth-service',
    status: 'running',
    createdAt: new Date(Date.now() - 15 * 60 * 1000).toISOString(),
    updatedAt: new Date(Date.now() - 2 * 60 * 1000).toISOString(),
    totalFindings: 3,
    currentStep: 's5',
    steps: [
      { id: 's1', name: 'repository_analyzer', label: 'Repository Analysis', status: 'completed', progress: 100, startedAt: new Date(Date.now() - 15 * 60 * 1000).toISOString(), completedAt: new Date(Date.now() - 13 * 60 * 1000).toISOString(), message: 'Repository structure analyzed' },
      { id: 's2', name: 'orchestrator', label: 'Orchestrator', status: 'completed', progress: 100, startedAt: new Date(Date.now() - 13 * 60 * 1000).toISOString(), completedAt: new Date(Date.now() - 12 * 60 * 1000).toISOString(), message: 'Analysis plan created' },
      { id: 's3', name: 'code_review', label: 'Code Review', status: 'completed', progress: 100, findingsCount: 1, startedAt: new Date(Date.now() - 12 * 60 * 1000).toISOString(), completedAt: new Date(Date.now() - 8 * 60 * 1000).toISOString(), message: '1 issue discovered' },
      { id: 's4', name: 'security', label: 'Security Analysis', status: 'completed', progress: 100, findingsCount: 2, startedAt: new Date(Date.now() - 12 * 60 * 1000).toISOString(), completedAt: new Date(Date.now() - 7 * 60 * 1000).toISOString(), message: '2 issues discovered' },
      { id: 's5', name: 'test_analysis', label: 'Test Analysis', status: 'running', progress: 65, startedAt: new Date(Date.now() - 7 * 60 * 1000).toISOString(), message: 'Analyzing edge cases...' },
      { id: 's6', name: 'documentation', label: 'Documentation', status: 'running', progress: 40, startedAt: new Date(Date.now() - 7 * 60 * 1000).toISOString(), message: 'Scanning docstrings...' },
      { id: 's7', name: 'finding_aggregation', label: 'Finding Aggregation', status: 'pending' },
      { id: 's8', name: 'fix_planning', label: 'Fix Planning', status: 'pending' },
      { id: 's9', name: 'human_approval', label: 'Human Approval', status: 'pending' },
      { id: 's10', name: 'testing', label: 'Testing', status: 'pending' },
      { id: 's11', name: 'verification', label: 'Verification', status: 'pending' },
      { id: 's12', name: 'final_report', label: 'Final Report', status: 'pending' },
    ],
  },
]

export const mockActiveWorkflow = mockWorkflows[1]
