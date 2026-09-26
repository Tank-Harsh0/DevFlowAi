import { useState, useCallback, useEffect } from 'react'
import { useSearchParams } from 'react-router-dom'
import { GitBranch } from 'lucide-react'

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { WorkflowStatusBadge } from '@/components/ui/status-badge'
import { LoadingState, ErrorState, EmptyState } from '@/components/ui/states'
import { MockDataNotice } from '@/components/ui/mock-notice'

import { WorkflowHeader } from '@/components/workflow/WorkflowHeader'
import { WorkflowSummary } from '@/components/workflow/WorkflowSummary'
import { WorkflowTimeline } from '@/components/workflow/WorkflowTimeline'
import { ConnectionStatus } from '@/components/workflow/ConnectionStatus'
import { ApprovalRequired } from '@/components/workflow/ApprovalRequired'
import { WorkflowError } from '@/components/workflow/WorkflowError'
import { WorkflowCompletion } from '@/components/workflow/WorkflowCompletion'
import { ActivityFeed } from '@/components/workflow/ActivityFeed'

import { useWorkflows } from '@/hooks/useWorkflows'
import { useWebSocket } from '@/hooks/useWebSocket'
import type { WorkflowRun, WorkflowEvent } from '@/types/workflow'

// ── Helpers ───────────────────────────────────────────────────────────────────

function formatDateTime(iso: string): string {
  return new Date(iso).toLocaleString('en-US', {
    month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit',
  })
}

// ── Workflow selector (left sidebar) ─────────────────────────────────────────

function WorkflowSelector({
  workflows,
  selected,
  onSelect,
}: {
  workflows: WorkflowRun[]
  selected: WorkflowRun
  onSelect: (wf: WorkflowRun) => void
}) {
  return (
    <nav aria-label="Workflow list" className="flex flex-col gap-1">
      {workflows.map((wf) => (
        <button
          key={wf.id}
          type="button"
          onClick={() => onSelect(wf)}
          aria-current={wf.id === selected.id ? 'true' : undefined}
          className={`w-full text-left px-3 py-2.5 rounded-md border text-sm transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring ${
            wf.id === selected.id
              ? 'border-primary/40 bg-primary/5 text-foreground'
              : 'border-transparent hover:bg-accent text-muted-foreground hover:text-foreground'
          }`}
        >
          <div className="flex items-center justify-between gap-2">
            <span className="font-medium truncate">{wf.repositoryName}</span>
            <WorkflowStatusBadge status={wf.status} />
          </div>
          <p className="text-xs text-muted-foreground mt-0.5">{formatDateTime(wf.createdAt)}</p>
        </button>
      ))}
    </nav>
  )
}

// ── Page ─────────────────────────────────────────────────────────────────────

export default function Workflow() {
  const [searchParams] = useSearchParams()
  const workflowIdParam = searchParams.get('workflowId')

  const { data: workflows, loading, error, isMock, refetch } = useWorkflows()
  const [selected, setSelected] = useState<WorkflowRun | null>(null)

  // When the URL carries a workflowId (e.g. navigated from Repositories after
  // starting a run), pre-select that workflow once the list has loaded.
  useEffect(() => {
    if (!workflowIdParam || !workflows.length) return
    const target = workflows.find((w) => w.id === workflowIdParam)
    if (target) setSelected(target)
  }, [workflowIdParam, workflows])

  // Prefer an explicit selection; fall back to first running, then first overall
  const activeWorkflow =
    selected ?? workflows.find((w) => w.status === 'running') ?? workflows[0] ?? null

  // Derive contextual state from the active workflow
  const isRunning = activeWorkflow?.status === 'running'
  const isFailed = activeWorkflow?.status === 'failed'
  const isCompleted = activeWorkflow?.status === 'completed'
  const isWaitingApproval = activeWorkflow?.status === 'waiting_approval'
  const approvalStep = activeWorkflow?.steps.find((s) => s.status === 'waiting_approval')
  const failedStep = activeWorkflow?.steps.find((s) => s.status === 'failed')

  // Live WebSocket updates — only enabled when running a real (non-mock) workflow
  const handleWsEvent = useCallback((event: WorkflowEvent) => {
    if (!activeWorkflow) return

    if (event.type === 'step_update' && event.step) {
      setSelected((prev) => {
        const wf = prev ?? activeWorkflow
        if (wf.id !== event.workflowId) return prev
        return {
          ...wf,
          steps: wf.steps.map((s) =>
            s.id === event.step!.id ? { ...s, ...event.step } : s
          ),
        }
      })
    } else if (event.type === 'workflow_update' && event.workflow) {
      setSelected((prev) => {
        const wf = prev ?? activeWorkflow
        if (wf.id !== event.workflowId) return prev
        return { ...wf, ...event.workflow }
      })
    }
  }, [activeWorkflow])

  const { status: wsStatus } = useWebSocket({
    workflowId: activeWorkflow?.id ?? null,
    onEvent: handleWsEvent,
    enabled: !isMock && isRunning,
  })

  // Feed all active/completed steps to the activity panel
  const feedSteps = activeWorkflow?.steps.filter(
    (s) => s.status !== 'pending'
  ) ?? []

  // ── Guards ──────────────────────────────────────────────────────────────────
  if (loading) return <LoadingState message="Loading workflows..." />
  if (error) return <ErrorState message={error} onRetry={refetch} />
  if (!activeWorkflow) {
    return (
      <EmptyState
        icon={GitBranch}
        title="No workflows yet"
        description="Start a workflow from the Repositories page to monitor agent activity here."
      />
    )
  }

  // ── Layout ──────────────────────────────────────────────────────────────────
  return (
    <div className="space-y-4">
      {/* Top bar: mock notice + WS connection status */}
      <div className="flex items-center gap-3 flex-wrap">
        <MockDataNotice isMock={isMock} />
        {!isMock && isRunning && (
          <ConnectionStatus status={wsStatus} />
        )}
      </div>

      {/* Main 4-column grid */}
      <div className="grid grid-cols-1 lg:grid-cols-4 gap-4">

        {/* ── Left col: workflow selector ── */}
        <Card className="lg:col-span-1 self-start">
          <CardHeader className="pb-3">
            <CardTitle>Workflows</CardTitle>
          </CardHeader>
          <CardContent className="p-3 pt-0">
            <WorkflowSelector
              workflows={workflows}
              selected={activeWorkflow}
              onSelect={setSelected}
            />
          </CardContent>
        </Card>

        {/* ── Center 2 cols: header + banners + timeline ── */}
        <div className="lg:col-span-2 flex flex-col gap-4">

          {/* Header: repo name, status badge, elapsed, refresh */}
          <Card>
            <CardContent className="p-4 flex flex-col gap-3">
              <WorkflowHeader
                workflow={activeWorkflow}
                onRefresh={refetch}
              />
              <div className="border-t border-border pt-3">
                <WorkflowSummary workflow={activeWorkflow} />
              </div>
            </CardContent>
          </Card>

          {/* Status banners — mutually exclusive based on workflow state */}
          {isWaitingApproval && (
            <ApprovalRequired
              stepLabel={approvalStep?.label}
              message={approvalStep?.message}
              workflowId={activeWorkflow.id}
            />
          )}
          {isFailed && (
            <WorkflowError
              failedStep={failedStep?.label}
              errorMessage={failedStep?.errorMessage}
              onRetry={refetch}
            />
          )}
          {isCompleted && (
            <WorkflowCompletion workflow={activeWorkflow} />
          )}

          {/* Timeline — full pipeline visualization */}
          <Card>
            <CardHeader className="pb-2">
              <CardTitle>Pipeline</CardTitle>
            </CardHeader>
            <CardContent className="pt-2">
              <WorkflowTimeline workflow={activeWorkflow} />
            </CardContent>
          </Card>
        </div>

        {/* ── Right col: live activity feed ── */}
        <Card className="lg:col-span-1 self-start">
          <CardHeader className="pb-3">
            <CardTitle>Activity</CardTitle>
          </CardHeader>
          <CardContent className="p-3 pt-0">
            <ActivityFeed steps={feedSteps} />
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
