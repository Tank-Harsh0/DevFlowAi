import type { WorkflowStatus } from '@/types/workflow'
import { cn } from '@/lib/utils'
import {
  CheckCircle2,
  Circle,
  Loader2,
  XCircle,
  SkipForward,
  Clock,
} from 'lucide-react'

interface AgentStep {
  id: string
  label: string
  status: WorkflowStatus
  progress?: number
  message?: string
  findingsCount?: number
}

const statusIcon: Record<WorkflowStatus, React.ReactNode> = {
  completed:        <CheckCircle2 className="w-4 h-4 text-success shrink-0" />,
  running:          <Loader2 className="w-4 h-4 text-warning shrink-0 animate-spin" />,
  failed:           <XCircle className="w-4 h-4 text-error shrink-0" />,
  pending:          <Circle className="w-4 h-4 text-muted-foreground/40 shrink-0" />,
  skipped:          <SkipForward className="w-4 h-4 text-muted-foreground/40 shrink-0" />,
  waiting_approval: <Clock className="w-4 h-4 text-info shrink-0" />,
}

interface AgentActivityItemProps {
  step: AgentStep
}

export function AgentActivityItem({ step }: AgentActivityItemProps) {
  return (
    <div className="flex items-start gap-3 py-2.5">
      <div className="mt-0.5">{statusIcon[step.status]}</div>
      <div className="flex-1 min-w-0">
        <div className="flex items-center justify-between gap-2">
          <p className={cn('text-sm font-medium truncate', step.status === 'pending' || step.status === 'skipped' ? 'text-muted-foreground' : 'text-foreground')}>
            {step.label}
          </p>
          {step.findingsCount !== undefined && step.findingsCount > 0 && (
            <span className="text-xs text-muted-foreground shrink-0">{step.findingsCount} issue{step.findingsCount !== 1 ? 's' : ''}</span>
          )}
        </div>
        {step.message && (
          <p className="text-xs text-muted-foreground mt-0.5 truncate">{step.message}</p>
        )}
        {step.status === 'running' && step.progress !== undefined && (
          <div className="mt-1.5 w-full bg-border rounded-full h-1">
            <div
              className="h-1 bg-warning rounded-full transition-all duration-500"
              style={{ width: `${step.progress}%` }}
            />
          </div>
        )}
      </div>
    </div>
  )
}


// ── Compact activity feed ──────────────────────────────────────────────────

export function AgentActivityFeed({ steps }: { steps: AgentStep[] }) {
  return (
    <div className="divide-y divide-border">
      {steps.map((step) => (
        <AgentActivityItem key={step.id} step={step} />
      ))}
    </div>
  )
}
