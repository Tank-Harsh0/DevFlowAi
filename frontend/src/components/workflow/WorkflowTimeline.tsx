import type { WorkflowRun, WorkflowStatus, AgentStep } from '@/types/workflow'
import { cn } from '@/lib/utils'
import {
  CheckCircle2,
  Circle,
  Loader2,
  XCircle,
  Clock,
  SkipForward,
  GitBranch,
  Brain,
  Layers,
  Code2,
  TestTube2,
  ShieldCheck,
  FileText,
  Merge,
  Wrench,
  UserCheck,
  FlaskConical,
  BadgeCheck,
  ScrollText,
  AlertCircle,
} from 'lucide-react'

// ── Pipeline definition ─────────────────────────────────────────────────────

const PIPELINE_STAGES: {
  ids: string[]
  label: string
  icon: React.ComponentType<{ className?: string }>
  parallel?: boolean
}[] = [
  { ids: ['repository_analyzer'], label: 'Repository Analysis', icon: GitBranch },
  { ids: ['orchestrator'],         label: 'Orchestrator',         icon: Brain },
  {
    ids: ['code_review', 'security', 'test_analysis', 'documentation'],
    label: 'Parallel Analysis',
    icon: Layers,
    parallel: true,
  },
  { ids: ['finding_aggregation'], label: 'Finding Aggregation', icon: Merge },
  { ids: ['fix_planning'],         label: 'Fix Planning',         icon: Wrench },
  { ids: ['human_approval'],       label: 'Human Approval',       icon: UserCheck },
  { ids: ['testing'],              label: 'Testing',               icon: FlaskConical },
  { ids: ['verification'],         label: 'Verification',          icon: BadgeCheck },
  { ids: ['final_report'],         label: 'Final Report',          icon: ScrollText },
]

const PARALLEL_AGENTS: {
  id: string
  label: string
  icon: React.ComponentType<{ className?: string }>
}[] = [
  { id: 'code_review',   label: 'Code Review',   icon: Code2 },
  { id: 'security',      label: 'Security',       icon: ShieldCheck },
  { id: 'test_analysis', label: 'Test Analysis',  icon: TestTube2 },
  { id: 'documentation', label: 'Documentation',  icon: FileText },
]

// ── Helpers ──────────────────────────────────────────────────────────────────

function getStepByName(steps: AgentStep[], name: string): AgentStep | undefined {
  return steps.find((s) => s.name === name)
}

function aggregateParallelStatus(steps: AgentStep[]): WorkflowStatus {
  if (steps.length === 0) return 'pending'
  const statuses = steps.map((s) => s.status)
  if (statuses.some((s) => s === 'failed')) return 'failed'
  if (statuses.some((s) => s === 'waiting_approval')) return 'waiting_approval'
  if (statuses.every((s) => s === 'completed')) return 'completed'
  if (statuses.every((s) => s === 'skipped')) return 'skipped'
  if (statuses.some((s) => s === 'running' || s === 'completed')) return 'running'
  return 'pending'
}

function formatDuration(startIso?: string, endIso?: string): string | null {
  if (!startIso) return null
  const start = new Date(startIso).getTime()
  const end = endIso ? new Date(endIso).getTime() : Date.now()
  const secs = Math.floor((end - start) / 1000)
  if (secs < 60) return `${secs}s`
  const mins = Math.floor(secs / 60)
  if (mins < 60) return `${mins}m ${secs % 60}s`
  return `${Math.floor(mins / 60)}h ${mins % 60}m`
}

function formatTime(iso?: string): string | null {
  if (!iso) return null
  return new Date(iso).toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit', second: '2-digit' })
}

// ── Status configuration ─────────────────────────────────────────────────────

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

const statusNodeClass: Record<WorkflowStatus, string> = {
  completed:        'border-success/40 bg-success/10',
  running:          'border-warning/40 bg-warning/10',
  failed:           'border-error/40 bg-error/10',
  pending:          'border-border bg-card',
  skipped:          'border-border bg-card',
  waiting_approval: 'border-info/40 bg-info/10',
}

const statusDotClass: Record<WorkflowStatus, string> = {
  completed:        'bg-success',
  running:          'bg-warning animate-pulse',
  failed:           'bg-error',
  pending:          'bg-border',
  skipped:          'bg-border',
  waiting_approval: 'bg-info animate-pulse',
}

// ── StageNode ────────────────────────────────────────────────────────────────

interface StageNodeProps {
  label: string
  icon: React.ComponentType<{ className?: string }>
  status: WorkflowStatus
  step?: AgentStep
  isLast?: boolean
  children?: React.ReactNode
}

function StageNode({ label, icon: Icon, status, step, isLast, children }: StageNodeProps) {
  const StatusIcon = statusIconMap[status]
  const duration = formatDuration(step?.startedAt, step?.completedAt)
  const startTime = formatTime(step?.startedAt)
  const isRunning = status === 'running'
  const isApproval = status === 'waiting_approval'

  return (
    <div className="relative flex gap-4">
      {/* Connector */}
      {!isLast && (
        <div className="absolute left-[17px] top-9 bottom-0 w-px bg-border" />
      )}

      {/* Stage icon circle */}
      <div className={cn(
        'relative z-10 flex items-center justify-center w-9 h-9 rounded-full border-2 shrink-0 mt-0.5',
        statusNodeClass[status]
      )}>
        <Icon className={cn('w-4 h-4', statusIconColor[status])} />
      </div>

      {/* Content */}
      <div className={cn('flex-1 pb-6 min-w-0', isLast && 'pb-2')}>
        {/* Header row */}
        <div className="flex items-center gap-2 flex-wrap min-h-[36px]">
          <span className={cn(
            'text-sm font-medium',
            status === 'pending' || status === 'skipped'
              ? 'text-muted-foreground'
              : 'text-foreground'
          )}>
            {label}
          </span>
          <StatusIcon className={cn(
            'w-3.5 h-3.5 shrink-0',
            statusIconColor[status],
            isRunning ? 'animate-spin' : ''
          )} />
          {duration && (
            <span className="text-[10px] text-muted-foreground ml-auto shrink-0 tabular-nums">
              {status === 'running' ? '⏱ ' : ''}{duration}
            </span>
          )}
        </div>

        {/* Start time */}
        {startTime && (
          <p className="text-[10px] text-muted-foreground -mt-2 mb-1.5">
            {status === 'running' ? 'Started ' : 'At '}{startTime}
          </p>
        )}

        {/* Step message */}
        {step?.message && (
          <p className="text-xs text-muted-foreground mb-2 leading-snug">{step.message}</p>
        )}

        {/* Progress bar for running step */}
        {isRunning && step?.progress !== undefined && (
          <div className="w-full bg-border rounded-full h-1 mb-2">
            <div
              className="h-1 bg-warning rounded-full transition-all duration-700"
              style={{ width: `${step.progress}%` }}
            />
          </div>
        )}

        {/* Error message */}
        {status === 'failed' && step?.errorMessage && (
          <div className="flex items-start gap-1.5 p-2 rounded-md bg-error/10 border border-error/20 mb-2">
            <AlertCircle className="w-3.5 h-3.5 text-error shrink-0 mt-0.5" />
            <p className="text-xs text-error leading-snug">{step.errorMessage}</p>
          </div>
        )}

        {/* Approval callout */}
        {isApproval && (
          <div className="flex items-start gap-1.5 p-2 rounded-md bg-info/10 border border-info/20 mb-2">
            <Clock className="w-3.5 h-3.5 text-info shrink-0 mt-0.5" />
            <p className="text-xs text-info leading-snug">
              Waiting for developer approval before proceeding.
            </p>
          </div>
        )}

        {/* Findings badge */}
        {step?.findingsCount !== undefined && step.findingsCount > 0 && (
          <span className="inline-flex items-center gap-1 text-[10px] font-medium text-amber-500 bg-amber-500/10 border border-amber-500/20 rounded-full px-2 py-0.5 mb-2">
            {step.findingsCount} finding{step.findingsCount !== 1 ? 's' : ''}
          </span>
        )}

        {children}
      </div>
    </div>
  )
}

// ── Parallel agent row (inside the Parallel Analysis section) ────────────────

interface ParallelAgentRowProps {
  step?: AgentStep
  label: string
  icon: React.ComponentType<{ className?: string }>
}

function ParallelAgentRow({ step, label, icon: Icon }: ParallelAgentRowProps) {
  const status: WorkflowStatus = step?.status ?? 'pending'
  const StatusIcon = statusIconMap[status]
  const duration = formatDuration(step?.startedAt, step?.completedAt)

  return (
    <div className="flex items-center gap-2.5 py-2 border-b border-border/50 last:border-b-0">
      <span className={cn('w-1.5 h-1.5 rounded-full shrink-0', statusDotClass[status])} />
      <Icon className="w-3.5 h-3.5 text-muted-foreground shrink-0" />
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-1.5">
          <span className={cn('text-xs font-medium', status === 'pending' ? 'text-muted-foreground' : 'text-foreground')}>
            {label}
          </span>
          <StatusIcon className={cn('w-3 h-3 shrink-0', statusIconColor[status], status === 'running' ? 'animate-spin' : '')} />
        </div>
        {step?.message && status === 'running' && (
          <p className="text-[10px] text-muted-foreground truncate mt-0.5">{step.message}</p>
        )}
      </div>
      <div className="flex items-center gap-2 shrink-0">
        {step?.findingsCount !== undefined && step.findingsCount > 0 && (
          <span className="text-[10px] text-amber-500 tabular-nums">{step.findingsCount}</span>
        )}
        {duration && (
          <span className="text-[10px] text-muted-foreground tabular-nums">{duration}</span>
        )}
      </div>
    </div>
  )
}

// ── Public export ────────────────────────────────────────────────────────────

export function WorkflowTimeline({ workflow }: { workflow: WorkflowRun }) {
  return (
    <div className="p-1">
      {PIPELINE_STAGES.map((stage, idx) => {
        const isLast = idx === PIPELINE_STAGES.length - 1

        if (stage.parallel) {
          const subSteps = PARALLEL_AGENTS
            .map((a) => getStepByName(workflow.steps, a.id))
            .filter(Boolean) as AgentStep[]
          const parallelStatus = aggregateParallelStatus(subSteps)

          return (
            <StageNode
              key="parallel"
              label={stage.label}
              icon={stage.icon}
              status={parallelStatus}
              isLast={isLast}
            >
              <div className="ml-1 pl-3 border-l border-border">
                {PARALLEL_AGENTS.map((agent) => (
                  <ParallelAgentRow
                    key={agent.id}
                    step={getStepByName(workflow.steps, agent.id)}
                    label={agent.label}
                    icon={agent.icon}
                  />
                ))}
              </div>
            </StageNode>
          )
        }

        const step = getStepByName(workflow.steps, stage.ids[0])
        return (
          <StageNode
            key={stage.ids[0]}
            label={stage.label}
            icon={stage.icon}
            status={step?.status ?? 'pending'}
            step={step}
            isLast={isLast}
          />
        )
      })}
    </div>
  )
}
