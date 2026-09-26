import type { WorkflowRun } from '@/types/workflow'
import { Layers, AlertTriangle, TestTube2, CheckCircle2 } from 'lucide-react'

interface WorkflowSummaryProps {
  workflow: WorkflowRun
}

function SummaryItem({
  icon: Icon,
  label,
  value,
  accent,
}: {
  icon: React.ComponentType<{ className?: string }>
  label: string
  value: string | number
  accent?: boolean
}) {
  return (
    <div className="flex items-center gap-2.5">
      <div className="flex items-center justify-center w-7 h-7 rounded-md bg-muted shrink-0">
        <Icon className="w-3.5 h-3.5 text-muted-foreground" />
      </div>
      <div>
        <p className="text-[10px] text-muted-foreground uppercase tracking-wide">{label}</p>
        <p className={`text-sm font-bold tabular-nums leading-tight ${accent ? 'text-success' : 'text-foreground'}`}>
          {value}
        </p>
      </div>
    </div>
  )
}

export function WorkflowSummary({ workflow }: WorkflowSummaryProps) {
  const completedSteps = workflow.steps.filter((s) => s.status === 'completed').length
  const totalSteps = workflow.steps.length
  const runningAgents = workflow.steps.filter((s) => s.status === 'running').length

  return (
    <div className="flex flex-wrap gap-5">
      <SummaryItem
        icon={Layers}
        label="Stages"
        value={`${completedSteps} / ${totalSteps}`}
      />
      {runningAgents > 0 && (
        <SummaryItem
          icon={Layers}
          label="Active"
          value={`${runningAgents} agent${runningAgents !== 1 ? 's' : ''}`}
        />
      )}
      {workflow.totalFindings !== undefined && (
        <SummaryItem
          icon={AlertTriangle}
          label="Findings"
          value={workflow.totalFindings}
        />
      )}
      {workflow.testsPassed !== undefined && (
        <SummaryItem
          icon={TestTube2}
          label="Tests"
          value={`${workflow.testsPassed} passed`}
          accent
        />
      )}
      {workflow.fixedFindings !== undefined && workflow.fixedFindings > 0 && (
        <SummaryItem
          icon={CheckCircle2}
          label="Fixed"
          value={workflow.fixedFindings}
          accent
        />
      )}
    </div>
  )
}
