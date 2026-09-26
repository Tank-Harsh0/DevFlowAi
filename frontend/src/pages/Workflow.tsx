import { useState, useCallback } from 'react'
import { Clock, GitBranch, Calendar } from 'lucide-react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { WorkflowStatusBadge } from '@/components/ui/status-badge'
import { WorkflowTimeline } from '@/components/workflow/WorkflowTimeline'
import { AgentActivityFeed } from '@/components/workflow/AgentActivityFeed'
import { LoadingState, ErrorState, EmptyState } from '@/components/ui/states'
import { MockDataNotice } from '@/components/ui/mock-notice'
import { useWorkflows } from '@/hooks/useWorkflows'
import { useWebSocket } from '@/hooks/useWebSocket'
import type { WorkflowRun, WorkflowEvent } from '@/types/workflow'

function formatDuration(startIso: string, endIso?: string): string {
  const start = new Date(startIso).getTime()
  const end = endIso ? new Date(endIso).getTime() : Date.now()
  const secs = Math.floor((end - start) / 1000)
  const mins = Math.floor(secs / 60)
  if (mins < 60) return `${mins}m ${secs % 60}s`
  return `${Math.floor(mins / 60)}h ${mins % 60}m`
}

function formatDateTime(iso: string): string {
  return new Date(iso).toLocaleString('en-US', {
    month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit',
  })
}

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
    <div className="flex flex-col gap-1.5">
      {workflows.map((wf) => (
        <button
          key={wf.id}
          type="button"
          onClick={() => onSelect(wf)}
          className={`w-full text-left px-3 py-2.5 rounded-md border text-sm transition-colors ${
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
    </div>
  )
}

export default function Workflow() {
  const { data: workflows, loading, error, isMock, refetch } = useWorkflows()
  const [selected, setSelected] = useState<WorkflowRun | null>(null)

  // Select the first running workflow, or the first workflow overall
  const activeWorkflow = selected ?? workflows.find((w) => w.status === 'running') ?? workflows[0] ?? null

  // WebSocket for live updates on the active workflow
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
    // Only connect when the workflow is actually running
    enabled: !isMock && activeWorkflow?.status === 'running',
  })

  const runningSteps = activeWorkflow?.steps.filter(
    (s) => s.status === 'running' || s.status === 'completed'
  ) ?? []

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

  return (
    <div className="space-y-4">
      <div className="flex items-center gap-3 flex-wrap">
        <MockDataNotice isMock={isMock} />
        {!isMock && activeWorkflow.status === 'running' && (
          <span className="text-xs text-muted-foreground flex items-center gap-1.5">
            <span className={`w-1.5 h-1.5 rounded-full shrink-0 ${
              wsStatus === 'connected' ? 'bg-success animate-pulse' :
              wsStatus === 'connecting' ? 'bg-amber-500 animate-pulse' : 'bg-error'
            }`} />
            WebSocket: {wsStatus}
          </span>
        )}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-4 gap-4">
        {/* Left sidebar — workflow selector */}
        <Card className="lg:col-span-1">
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

        {/* Center — timeline */}
        <Card className="lg:col-span-2">
          <CardHeader className="pb-3">
            <div>
              <CardTitle className="flex items-center gap-2">
                <GitBranch className="w-4 h-4 text-muted-foreground" />
                {activeWorkflow.repositoryName}
              </CardTitle>
              <div className="flex items-center gap-4 mt-2 flex-wrap">
                <WorkflowStatusBadge status={activeWorkflow.status} />
                <span className="text-xs text-muted-foreground flex items-center gap-1">
                  <Calendar className="w-3 h-3" />
                  {formatDateTime(activeWorkflow.createdAt)}
                </span>
                <span className="text-xs text-muted-foreground flex items-center gap-1">
                  <Clock className="w-3 h-3" />
                  {formatDuration(activeWorkflow.createdAt, activeWorkflow.completedAt)}
                </span>
              </div>
            </div>
          </CardHeader>
          <CardContent className="pt-0">
            <WorkflowTimeline workflow={activeWorkflow} />
          </CardContent>
        </Card>

        {/* Right sidebar — step log */}
        <Card className="lg:col-span-1">
          <CardHeader className="pb-3">
            <CardTitle>Step Log</CardTitle>
          </CardHeader>
          <CardContent className="p-0 px-4 pb-4">
            <AgentActivityFeed steps={runningSteps} />
          </CardContent>
        </Card>
      </div>

      {/* Summary row */}
      {activeWorkflow.status === 'completed' && (
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
          <SummaryCard label="Total Findings" value={activeWorkflow.totalFindings ?? 0} />
          <SummaryCard label="Issues Fixed"   value={activeWorkflow.fixedFindings ?? 0} positive />
          <SummaryCard label="Tests Generated" value={activeWorkflow.testsGenerated ?? 0} positive />
          <SummaryCard label="Tests Passed"   value={activeWorkflow.testsPassed ?? 0} positive />
        </div>
      )}
    </div>
  )
}

function SummaryCard({ label, value, positive }: { label: string; value: number; positive?: boolean }) {
  return (
    <Card>
      <CardContent className="p-4">
        <p className="text-xs font-medium text-muted-foreground uppercase tracking-wide mb-1">{label}</p>
        <p className={`text-2xl font-bold tabular-nums ${positive ? 'text-success' : 'text-foreground'}`}>{value}</p>
      </CardContent>
    </Card>
  )
}
