// MOCK DATA — for UI development only.
// This data is NOT real AI analysis. It will be replaced by backend API responses in Phase 3.

import type { Report } from '@/types/report'

export const mockReports: Report[] = [
  {
    id: 'r-1',
    workflowId: 'wf-1',
    repositoryId: 'repo-1',
    repositoryName: 'todo-api',
    generatedAt: new Date(Date.now() - 90 * 60 * 1000).toISOString(),
    sections: {
      repository: {
        name: 'todo-api',
        url: 'https://github.com/acme/todo-api',
        technologies: ['Python 3.11', 'FastAPI', 'PostgreSQL', 'SQLAlchemy'],
        filesAnalyzed: 47,
        branch: 'main',
      },
      analysis: {
        totalIssues: 6,
        severityBreakdown: { critical: 1, high: 2, medium: 2, low: 1 },
        agentsUsed: ['Code Review', 'Security', 'Test Analysis', 'Documentation'],
        durationSeconds: 1800,
      },
      remediation: {
        issuesFixed: 2,
        filesModified: 3,
        developerApprovals: 2,
      },
      testing: {
        beforeCount: 18,
        generatedCount: 7,
        afterCount: 25,
        passed: 25,
        failed: 0,
        skipped: 0,
      },
      productivity: {
        manualDurationMinutes: 120,
        aiDurationMinutes: 27,
        timeSavedMinutes: 93,
        reductionPercent: 77.5,
        manualSteps: 14,
        automatedSteps: 11,
        developerInterventions: 2,
        issuesDetected: 6,
        issuesFixed: 2,
        testsGenerated: 7,
        reworkIterations: 0,
      },
    },
  },
]
