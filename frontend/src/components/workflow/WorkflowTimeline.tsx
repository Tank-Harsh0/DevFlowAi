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
} from 'lucide-react'

// Ordered display pipeline (some steps run in parallel)
const PIPELINE_STAGES: { ids: string[]; label: string; icon: React.ComponentType<{ className?: string }>; parallel?: boolean }[] = [
  { ids: ['repository_analyzer'], label: 'Repository Analysis',   icon: GitBranch },
  { ids: ['orchestrator'],         label: 'Orchestrator',           icon: Brain },
  {
    ids: ['code_review', 'security', 'test_analysis', 'documentation'],
    label: 'Parallel Analysis',
    icon: Layers,
    parallel: true,
  },
  { ids: ['finding_aggregation'], label: 'Finding Aggregation',   icon: Merge },
  { ids: ['fix_planning'],         label: 'Fix Planning',           icon: Wrench },
  { ids: ['human_approval'],       label: 'Human Approval',         icon: UserCheck },
  { ids: ['testing'],              label: 'Testing',                icon: FlaskConical },
  { ids: ['verification'],         label: 'Verification',           icon: BadgeCheck },
  { ids: ['final_report'],         label: 'Final Report',           icon: ScrollText },
]

const PARALLEL_AGENTS: { id: string; label: string; icon: React.ComponentType<{ className?: string }> }[] = [
  { id: 'code_review',    label: 'Code Review',    icon: Code2 },
  { id: 'security',       label: 'Security',       icon: ShieldCheck },
  { id: 'test_analysis',  label: 'Test Analysis',  icon: TestTube2 },
  { id: 'documentation',  label: 'Documentation',  icon: FileText },
]

function getStepByName(steps: AgentStep[], name: string): AgentStep | undefined {
  return steps.find((s) => s.name === name)
}

function aggregateParallelStatus(steps: AgentStep[]): WorkflowStatus {
  const statuses = steps.map((s) => s.status)
  if (statuses.some((s) => s === 'failed')) return 'failed'
  if (statuses.some((s) => s === 'running')) return 'running'
  if (statuses.every((s) => s === 'completed')) return 'completed'
  if (statuses.every((s) => s === 'skipped')) return 'skipped'
  if (statuses.some((s) => s === 'running' || s === 'completed')) return 'running'
  return 'pending'
}

const statusDotClass: Record<WorkflowStatus, string> = {
  completed:        'bg-success',
  running:          'bg-warning animate-pulse',
  failed:           'bg-error',
  pending:          'bg-border',
  skipped:          'bg-border',
  waiting_approval: 'bg-info animate-pulse',
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

interface StageNodeProps {
  label: string
  icon: React.ComponentType<{ className?: string }>
  status: WorkflowStatus
  message?: string
  isLast?: boolean
  children?: React.ReactNode
}

function StageNode({ label, icon: Icon, status, message, isLast, children }: StageNodeProps) {
  const StatusIcon = statusIconMap[status]
  return (
    <div className="relative flex gap-4">
      {/* Connector line */}
      {!isLast && (
        <div className="absolute left-[17px] top-8 bottom-0 w-px bg-border" />
      )}
      {/* Icon */}
      <div className={cn(
        'relative z-10 flex items-center justify-center w-9 h-9 rounded-full border-2 shrink-0',
        status === 'completed' ? 'border-success/40 bg-success/10' :
        status === 'running'   ? 'border-warning/40 bg-warning/10' :
        status === 'failed'    ? 'border-error/40 bg-error/10' :
        status === 'waiting_approval' ? 'border-info/40 bg-info/10' :
        'border-border bg-card'
      )}>
        <Icon className={cn('w-4 h-4', statusIconColor[status])} />
      </div>
      {/* Content */}
      <div className="flex-1 pb-6 min-w-0">
        <div className="flex items-center gap-2 h-9">
          <span className={cn('text-sm font-medium', status === 'pending' ? 'text-muted-foreground' : 'text-foreground')}>
            {label}
          </span>
          <StatusIcon className={cn('w-3.5 h-3.5 shrink-0', statusIconColor[status], status === 'running' ? 'animate-spin' : '')} />
        </div>
        {message && <p className="text-xs text-muted-foreground -mt-1 mb-2">{message}</p>}
        {children}
      </div>
    </div>
  )
}

interface ParallelAgentRowProps {
  step?: AgentStep
  label: string
  icon: React.ComponentType<{ className?: string }>
}

function ParallelAgentRow({ step, label, icon: Icon }: ParallelAgentRowProps) {
  const status: WorkflowStatus = step?.status ?? 'pending'
  const StatusIcon = statusIconMap[status]
  return (
    <div className="flex items-center gap-2.5 py-1.5">
      <span className={cn('w-1.5 h-1.5 rounded-full shrink-0', statusDotClass[status])} />
      <Icon className="w-3.5 h-3.5 text-muted-foreground shrink-0" />
      <span className={cn('text-xs', status === 'pending' ? 'text-muted-foreground' : 'text-foreground')}>{label}</span>
      <StatusIcon className={cn('w-3 h-3 ml-auto shrink-0', statusIconColor[status], status === 'running' ? 'animate-spin' : '')} />
      {step?.findingsCount !== undefined && step.findingsCount > 0 && (
        <span className="text-xs text-muted-foreground">{step.findingsCount}</span>
      )}
    </div>
  )
}

export function WorkflowTimeline({ workflow }: { workflow: WorkflowRun }) {
  return (
    <div className="p-1">
      {PIPELINE_STAGES.map((stage, idx) => {
        const isLast = idx === PIPELINE_STAGES.length - 1

        if (stage.parallel) {
          // Aggregate parallel status from all sub-agents
          const subSteps = PARALLEL_AGENTS.map((a) => getStepByName(workflow.steps, a.id)).filter(Boolean) as AgentStep[]
          const parallelStatus = aggregateParallelStatus(subSteps)
          const primaryMessage = subSteps.find((s) => s.status === 'running')?.message
          return (
            <StageNode key="parallel" label={stage.label} icon={stage.icon} status={parallelStatus} message={primaryMessage} isLast={isLast}>
              <div className="ml-1 pl-3 border-l border-border space-y-0.5">
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
        const status: WorkflowStatus = step?.status ?? 'pending'
        return (
          <StageNode
            key={stage.ids[0]}
            label={stage.label}
            icon={stage.icon}
            status={status}
            message={step?.message}
            isLast={isLast}
          />
        )
      })}
    </div>
  )
}
