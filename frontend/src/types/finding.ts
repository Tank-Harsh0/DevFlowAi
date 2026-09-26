// NOTE: These types are pending backend API confirmation.
// Inferred from docs/ARCHITECTURE.md data schemas.

export type FindingSeverity = 'critical' | 'high' | 'medium' | 'low'
export type FindingStatus = 'open' | 'fixed' | 'dismissed' | 'pending_fix'

export type AgentSource =
  | 'code_review'
  | 'test_analysis'
  | 'security'
  | 'documentation'

export interface FindingLocation {
  file: string
  line?: number
  endLine?: number
  column?: number
}

export interface CodeDiff {
  before: string
  after: string
  language?: string
}

export interface FixProposal {
  id: string
  findingId: string
  description: string
  reason: string
  risk: 'low' | 'medium' | 'high'
  diff?: CodeDiff
  affectedFiles: string[]
  approvedAt?: string
  rejectedAt?: string
}

export interface Finding {
  id: string
  workflowId: string
  severity: FindingSeverity
  status: FindingStatus
  agent: AgentSource
  title: string
  description: string
  location: FindingLocation
  evidence?: string
  whyItMatters?: string
  suggestedFix?: string
  verificationMethod?: string
  fixProposal?: FixProposal
  createdAt: string
  updatedAt: string
}
