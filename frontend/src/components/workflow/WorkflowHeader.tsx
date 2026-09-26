import { GitBranch, Clock, Calendar, RefreshCw } from 'lucide-react'
import type { WorkflowRun } from '@/types/workflow'
import { WorkflowStatusBadge } from '@/components/ui/status-badge'
import { Button } from '@/components/ui/button'
import { cn } from '@/lib/utils'

function formatRelativeTime(iso: string): string {
  const diff = Date.now() - new Date(iso).getTime()
  const secs = Math.floor(diff / 1000)
  if (secs < 60) return `${secs}s ago`
  const mins = Math.floor(secs / 60)
  if (mins < 60) return `${mins}m ago`
  const hrs = Math.floor(mins / 60)
  if (hrs < 24) return `${hrs}h ago`
  return `${Math.floor(hrs / 24)}d ago`
}

function formatElapsed(startIso: string, endIso?: string): string {
  const start = new Date(startIso).getTime()
  const end = endIso ? new Date(endIso).getTime() : Date.now()
  const secs = Math.floor((end - start) / 1000)
  if (secs < 60) return `${secs}s`
  const mins = Math.floor(secs / 60)
  if (mins < 60) return `${mins}m ${secs % 60}s`
  return `${Math.floor(mins / 60)}h ${mins % 60}m`
}

interface WorkflowHeaderProps {
  workflow: WorkflowRun
  onRefresh?: () => void
  className?: string
}

export function WorkflowHeader({ workflow, onRefresh, className }: WorkflowHeaderProps) {
  const isRunning = workflow.status === 'running'

  return (
    <div className={cn('flex items-start justify-between gap-4', className)}>
      <div className="min-w-0 flex-1">
        {/* Repo name + status */}
        <div className="flex items-center gap-3 flex-wrap">
          <div className="flex items-center gap-2">
            <GitBranch className="w-4 h-4 text-muted-foreground shrink-0" />
            <h2 className="text-base font-semibold text-foreground">{workflow.repositoryName}</h2>
          </div>
          <WorkflowStatusBadge status={workflow.status} />
        </div>

        {/* Metadata row */}
        <div className="flex items-center gap-4 mt-2 flex-wrap">
          <span className="text-xs text-muted-foreground flex items-center gap-1">
            <Calendar className="w-3 h-3" />
            Started {formatRelativeTime(workflow.createdAt)}
          </span>
          <span className="text-xs text-muted-foreground flex items-center gap-1">
            <Clock className="w-3 h-3" />
            {isRunning ? 'Running for ' : 'Duration: '}
            {formatElapsed(workflow.createdAt, workflow.completedAt)}
          </span>
          {workflow.currentStep && isRunning && (
            <span className="text-xs text-muted-foreground">
              Current: <span className="text-foreground font-medium">{workflow.currentStep}</span>
            </span>
          )}
        </div>
      </div>

      {/* Actions */}
      {onRefresh && (
        <Button
          variant="ghost"
          size="icon"
          aria-label="Refresh workflow"
          onClick={onRefresh}
          className="text-muted-foreground shrink-0"
        >
          <RefreshCw className="w-4 h-4" />
        </Button>
      )}
    </div>
  )
}
