// NOTE: These types are pending backend API confirmation.

export interface TestMetrics {
  beforeCount: number
  generatedCount: number
  afterCount: number
  passed: number
  failed: number
  skipped: number
}

export interface ProductivityMetrics {
  manualDurationMinutes: number
  aiDurationMinutes: number
  timeSavedMinutes: number
  reductionPercent: number
  manualSteps: number
  automatedSteps: number
  developerInterventions: number
  issuesDetected: number
  issuesFixed: number
  testsGenerated: number
  reworkIterations: number
}

export interface SeverityBreakdown {
  critical: number
  high: number
  medium: number
  low: number
}

export interface ReportSection {
  repository: {
    name: string
    url: string
    technologies: string[]
    filesAnalyzed: number
    branch: string
  }
  analysis: {
    totalIssues: number
    severityBreakdown: SeverityBreakdown
    agentsUsed: string[]
    durationSeconds: number
  }
  remediation: {
    issuesFixed: number
    filesModified: number
    developerApprovals: number
  }
  testing: TestMetrics
  productivity: ProductivityMetrics
}

export interface Report {
  id: string
  workflowId: string
  repositoryId: string
  repositoryName: string
  generatedAt: string
  sections: ReportSection
  downloadUrl?: string
}
