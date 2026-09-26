// NOTE: These types are pending backend API confirmation.
// Marked with @pending where the schema is inferred from docs/ARCHITECTURE.md.

export type WorkflowStatus =
  | 'pending'
  | 'running'
  | 'completed'
  | 'failed'
  | 'skipped'
  | 'waiting_approval'

export type AgentName =
  | 'repository_analyzer'
  | 'orchestrator'
  | 'code_review'
  | 'test_analysis'
  | 'security'
  | 'documentation'
  | 'finding_aggregation'
  | 'fix_planning'
  | 'human_approval'
  | 'testing'
  | 'verification'
  | 'final_report'

export interface AgentStep {
  id: string
  name: AgentName | string
  label: string
  status: WorkflowStatus
  progress?: number          // 0–100
  startedAt?: string         // ISO 8601
  completedAt?: string       // ISO 8601
  findingsCount?: number
  message?: string
  errorMessage?: string
}

export interface WorkflowRun {
  id: string
  repositoryId: string
  repositoryName: string
  status: WorkflowStatus
  createdAt: string
  updatedAt: string
  completedAt?: string
  steps: AgentStep[]
  totalFindings?: number
  fixedFindings?: number
  testsGenerated?: number
  testsPassed?: number
  currentStep?: string
}

export interface WorkflowEvent {
  type: 'step_update' | 'workflow_update' | 'log'
  workflowId: string
  step?: AgentStep
  workflow?: Partial<WorkflowRun>
  message?: string
  timestamp: string
}
