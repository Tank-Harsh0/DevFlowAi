// NOTE: These types are pending backend API confirmation.
// Inferred from docs/ARCHITECTURE.md data schemas.
// @pending — marked fields may change once the backend is implemented.

export type FindingSeverity = 'critical' | 'high' | 'medium' | 'low' | 'info'

export type FindingStatus =
  | 'open'           // Detected, no action taken
  | 'in_review'      // Under active human review
  | 'approved'       // Fix approved, pending execution
  | 'rejected'       // Fix rejected by developer
  | 'pending_fix'    // Approved, fix being applied
  | 'fixed'          // Fix applied successfully
  | 'verified'       // Fix verified by test run
  | 'verification_failed' // Verification test failed
  | 'dismissed'      // Finding dismissed without fix

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
  /** Function or method name, if provided by the backend */
  function?: string
}

export interface CodeDiff {
  before: string
  after: string
  /** Programming language hint for syntax highlighting */
  language?: string
}

/** A code snippet shown in the context of the finding */
export interface CodeSnippet {
  content: string
  startLine: number
  language?: string
  /** Lines to highlight (1-based relative to startLine) */
  highlightLines?: number[]
}

export interface FixProposal {
  id: string
  findingId: string
  description: string
  reason: string
  /** @pending — backend uses 'safe' | 'moderate' | 'high', mapped from architecture docs */
  risk: 'low' | 'medium' | 'high'
  diff?: CodeDiff
  affectedFiles: string[]
  approvedAt?: string
  rejectedAt?: string
  rejectionReason?: string
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
  /** Raw evidence string from the agent (e.g. problematic code line) */
  evidence?: string
  /** Code snippet with context, if provided by the backend */
  codeSnippet?: CodeSnippet
  whyItMatters?: string
  suggestedFix?: string
  verificationMethod?: string
  fixProposal?: FixProposal
  createdAt: string
  updatedAt: string
}
