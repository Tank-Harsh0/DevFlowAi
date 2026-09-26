/**
 * MOCK WORKFLOW EVENTS — Development only.
 *
 * This module provides a simulated event stream for testing the
 * Workflow page without a live WebSocket backend.
 *
 * It is NEVER used in production code. It must only be imported
 * explicitly by a developer during local testing.
 *
 * Usage (in a dev-only context):
 *   import { createMockEventStream } from '@/mocks/workflowEvents'
 *   const stop = createMockEventStream('wf-2', (event) => handleEvent(event))
 *   // later: stop()
 */

import type { WorkflowEvent, AgentStep, WorkflowStatus } from '@/types/workflow'

interface MockStepUpdate {
  stepId: string
  name: string
  label: string
  status: WorkflowStatus
  message?: string
  progress?: number
  findingsCount?: number
}

const DEMO_SEQUENCE: MockStepUpdate[] = [
  { stepId: 's5', name: 'test_analysis',  label: 'Test Analysis',  status: 'running',   progress: 70,  message: 'Analyzing edge cases...' },
  { stepId: 's6', name: 'documentation',  label: 'Documentation',  status: 'running',   progress: 55,  message: 'Scanning docstrings...' },
  { stepId: 's5', name: 'test_analysis',  label: 'Test Analysis',  status: 'running',   progress: 90,  message: 'Generating test stubs...' },
  { stepId: 's5', name: 'test_analysis',  label: 'Test Analysis',  status: 'completed', message: '1 issue discovered', findingsCount: 1 },
  { stepId: 's6', name: 'documentation',  label: 'Documentation',  status: 'running',   progress: 85,  message: 'Checking endpoint docs...' },
  { stepId: 's6', name: 'documentation',  label: 'Documentation',  status: 'completed', message: '1 issue discovered', findingsCount: 1 },
  { stepId: 's7', name: 'finding_aggregation', label: 'Finding Aggregation', status: 'running', message: 'Aggregating 4 findings...' },
  { stepId: 's7', name: 'finding_aggregation', label: 'Finding Aggregation', status: 'completed', message: '4 total findings aggregated' },
  { stepId: 's8', name: 'fix_planning',   label: 'Fix Planning',   status: 'running',   message: 'Generating fix proposals...' },
  { stepId: 's8', name: 'fix_planning',   label: 'Fix Planning',   status: 'completed', message: '2 fix proposals generated' },
  { stepId: 's9', name: 'human_approval', label: 'Human Approval', status: 'waiting_approval', message: 'Awaiting developer review' },
]

/**
 * Creates a simulated event stream for the given workflowId.
 * Fires events at realistic intervals.
 * Returns a cleanup function.
 */
export function createMockEventStream(
  workflowId: string,
  onEvent: (event: WorkflowEvent) => void
): () => void {
  const timers: ReturnType<typeof setTimeout>[] = []
  let delay = 1000

  for (const update of DEMO_SEQUENCE) {
    const step: AgentStep = {
      id: update.stepId,
      name: update.name,
      label: update.label,
      status: update.status,
      message: update.message,
      progress: update.progress,
      findingsCount: update.findingsCount,
      startedAt: new Date().toISOString(),
      ...(update.status === 'completed' ? { completedAt: new Date().toISOString() } : {}),
    }

    const t = setTimeout(() => {
      onEvent({
        type: 'step_update',
        workflowId,
        step,
        timestamp: new Date().toISOString(),
      })
    }, delay)

    timers.push(t)
    delay += update.status === 'running' ? 1500 : 2500
  }

  return () => timers.forEach(clearTimeout)
}
