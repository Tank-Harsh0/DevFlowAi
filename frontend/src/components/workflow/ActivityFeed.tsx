import { useRef, useEffect } from 'react'
import type { AgentStep, WorkflowStatus } from '@/types/workflow'
import {
  CheckCircle2, Circle, Loader2, XCircle, Clock, SkipForward,
} from 'lucide-react'
import { cn } from '@/lib/utils'

// ── Status helpers ────────────────────────────────────────────────────────────

const statusIconMap: Record<WorkflowStatus, React.ComponentType<{ className?: string }>> = {
  completed:        CheckCircle2,
  running:          Loader2,
  failed:           XCircle,
  pending:          Circle,
  skipped:          SkipForward,
  waiting_approval: Clock,
}

const statusIconColor: Record<WorkflowStatus, string> = {
  completed:        'text-success',
  running:          'text-warning',
  failed:           'text-error',
  pending:          'text-muted-foreground/40',
  skipped:          'text-muted-foreground/40',
  waiting_approval: 'text-info',
}

function formatTime(iso?: string): string | null {
  if (!iso) return null
  return new Date(iso).toLocaleTimeString('en-US', {
    hour: '2-digit', minute: '2-digit', second: '2-digit',
  })
}

// ── ActivityItem ──────────────────────────────────────────────────────────────

interface ActivityItemProps {
  step: AgentStep
}

function ActivityItem({ step }: ActivityItemProps) {
  const status = step.status
  const StatusIcon = statusIconMap[status]
  const time = formatTime(step.completedAt ?? step.startedAt)

  return (
    <div className="flex gap-2.5 py-2.5 border-b border-border last:border-b-0">
      {/* Timestamp column */}
      <div className="w-14 shrink-0 pt-0.5">
        {time && (
          <span className="text-[10px] text-muted-foreground/60 font-mono tabular-nums">{time}</span>
        )}
      </div>

      {/* Icon */}
      <StatusIcon className={cn(
        'w-3.5 h-3.5 shrink-0 mt-0.5',
        statusIconColor[status],
        status === 'running' ? 'animate-spin' : ''
      )} />

      {/* Content */}
      <div className="flex-1 min-w-0">
        <p className={cn(
          'text-xs font-medium leading-snug',
          status === 'pending' ? 'text-muted-foreground' : 'text-foreground'
        )}>
          {step.label}
        </p>
        {step.message && (
          <p className="text-[10px] text-muted-foreground mt-0.5 leading-snug">{step.message}</p>
        )}
        {step.findingsCount !== undefined && step.findingsCount > 0 && (
          <span className="inline-flex items-center mt-0.5 text-[10px] text-amber-500">
            {step.findingsCount} finding{step.findingsCount !== 1 ? 's' : ''}
          </span>
        )}
      </div>
    </div>
  )
}

// ── ActivityFeed ──────────────────────────────────────────────────────────────

interface ActivityFeedProps {
  /** Steps to show — caller decides how many/which to pass */
  steps: AgentStep[]
  /** Max items visible before scrolling; default 12 */
  maxVisible?: number
}

export function ActivityFeed({ steps, maxVisible = 12 }: ActivityFeedProps) {
  const scrollRef = useRef<HTMLDivElement>(null)

  // Auto-scroll to bottom when new items arrive
  useEffect(() => {
    const el = scrollRef.current
    if (el) el.scrollTop = el.scrollHeight
  }, [steps.length])

  const visible = steps.slice(-maxVisible)

  if (visible.length === 0) {
    return (
      <p className="text-xs text-muted-foreground py-4 text-center">
        No activity yet.
      </p>
    )
  }

  return (
    <div
      ref={scrollRef}
      className="overflow-y-auto scrollbar-thin max-h-80"
      role="log"
      aria-label="Agent activity feed"
      aria-live="polite"
      aria-atomic="false"
    >
      {visible.map((step) => (
        <ActivityItem key={step.id} step={step} />
      ))}
    </div>
  )
}
