import type { AgentStep, WorkflowStatus } from '@/types/workflow'
import {
  CheckCircle2, Circle, Loader2, XCircle, Clock, SkipForward,
  Code2, TestTube2, ShieldCheck, FileText,
} from 'lucide-react'
import { cn } from '@/lib/utils'

// ── Helpers ──────────────────────────────────────────────────────────────────

function formatDuration(startIso?: string, endIso?: string): string | null {
  if (!startIso) return null
  const start = new Date(startIso).getTime()
  const end = endIso ? new Date(endIso).getTime() : Date.now()
  const secs = Math.floor((end - start) / 1000)
  if (secs < 60) return `${secs}s`
  const mins = Math.floor(secs / 60)
  return `${mins}m ${secs % 60}s`
}

// ── Config ───────────────────────────────────────────────────────────────────

const agentConfig: Record<string, {
  label: string
  icon: React.ComponentType<{ className?: string }>
}> = {
  code_review:    { label: 'Code Review',    icon: Code2 },
  security:       { label: 'Security',       icon: ShieldCheck },
  test_analysis:  { label: 'Test Analysis',  icon: TestTube2 },
  documentation:  { label: 'Documentation',  icon: FileText },
}

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

const statusLabel: Record<WorkflowStatus, string> = {
  completed:        'Completed',
  running:          'Running',
  failed:           'Failed',
  pending:          'Pending',
  skipped:          'Skipped',
  waiting_approval: 'Waiting for approval',
}

const statusBorderClass: Record<WorkflowStatus, string> = {
  completed:        'border-success/30',
  running:          'border-warning/30 bg-warning/5',
  failed:           'border-error/30',
  pending:          'border-border',
  skipped:          'border-border opacity-60',
  waiting_approval: 'border-info/30 bg-info/5',
}

// ── AgentCard ────────────────────────────────────────────────────────────────

interface AgentCardProps {
  agentId: string
  step?: AgentStep
}

export function AgentCard({ agentId, step }: AgentCardProps) {
  const status: WorkflowStatus = step?.status ?? 'pending'
  const cfg = agentConfig[agentId] ?? { label: agentId, icon: Circle }
  const Icon = cfg.icon
  const StatusIcon = statusIconMap[status]
  const duration = formatDuration(step?.startedAt, step?.completedAt)
  const isRunning = status === 'running'

  return (
    <div className={cn(
      'rounded-lg border p-3.5 flex flex-col gap-2.5 transition-colors',
      statusBorderClass[status]
    )}>
      {/* Header */}
      <div className="flex items-center justify-between gap-2">
        <div className="flex items-center gap-2">
          <Icon className="w-4 h-4 text-muted-foreground shrink-0" />
          <span className="text-xs font-semibold text-foreground">{cfg.label}</span>
        </div>
        <StatusIcon className={cn(
          'w-3.5 h-3.5 shrink-0',
          statusIconColor[status],
          isRunning ? 'animate-spin' : ''
        )} />
      </div>

      {/* Status label */}
      <p className={cn('text-[10px] font-medium uppercase tracking-wide', statusIconColor[status])}>
        {statusLabel[status]}
      </p>

      {/* Running: message + progress */}
      {isRunning && step?.message && (
        <p className="text-xs text-muted-foreground leading-snug">{step.message}</p>
      )}
      {isRunning && step?.progress !== undefined && (
        <div className="w-full bg-border rounded-full h-1">
          <div
            className="h-1 bg-warning rounded-full transition-all duration-700"
            style={{ width: `${step.progress}%` }}
          />
        </div>
      )}

      {/* Completed: findings + duration */}
      {(status === 'completed' || status === 'failed') && (
        <div className="flex items-center justify-between gap-2">
          {step?.findingsCount !== undefined && step.findingsCount > 0 ? (
            <span className="text-[10px] font-medium text-amber-500">
              {step.findingsCount} finding{step.findingsCount !== 1 ? 's' : ''}
            </span>
          ) : status === 'completed' ? (
            <span className="text-[10px] text-muted-foreground">No findings</span>
          ) : (
            <span className="text-[10px] text-error">
              {step?.errorMessage ?? 'Error occurred'}
            </span>
          )}
          {duration && (
            <span className="text-[10px] text-muted-foreground tabular-nums">{duration}</span>
          )}
        </div>
      )}
    </div>
  )
}

// ── AgentGrid ────────────────────────────────────────────────────────────────

const PARALLEL_AGENT_IDS = ['code_review', 'security', 'test_analysis', 'documentation']

interface AgentGridProps {
  steps: AgentStep[]
}

export function AgentGrid({ steps }: AgentGridProps) {
  function getStep(agentId: string) {
    return steps.find((s) => s.name === agentId)
  }

  return (
    <div className="grid grid-cols-2 gap-2">
      {PARALLEL_AGENT_IDS.map((id) => (
        <AgentCard key={id} agentId={id} step={getStep(id)} />
      ))}
    </div>
  )
}
