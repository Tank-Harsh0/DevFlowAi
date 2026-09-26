import type { WorkflowStatus } from '@/types/workflow'
import type { FindingStatus, FindingSeverity } from '@/types/finding'
import { cn } from '@/lib/utils'

// ── Workflow status badge ──────────────────────────────────────────────────

const workflowStatusConfig: Record<WorkflowStatus, { label: string; classes: string; dot: string }> = {
  pending:          { label: 'Pending',          classes: 'bg-muted text-muted-foreground',               dot: 'bg-muted-foreground' },
  running:          { label: 'Running',           classes: 'bg-warning/10 text-warning border-warning/20', dot: 'bg-warning animate-pulse' },
  completed:        { label: 'Completed',         classes: 'bg-success/10 text-success border-success/20', dot: 'bg-success' },
  failed:           { label: 'Failed',            classes: 'bg-error/10 text-error border-error/20',       dot: 'bg-error' },
  skipped:          { label: 'Skipped',           classes: 'bg-muted text-muted-foreground',               dot: 'bg-muted-foreground' },
  waiting_approval: { label: 'Needs Approval',    classes: 'bg-info/10 text-info border-info/20',          dot: 'bg-info animate-pulse' },
}

interface WorkflowStatusBadgeProps {
  status: WorkflowStatus
  className?: string
}

export function WorkflowStatusBadge({ status, className }: WorkflowStatusBadgeProps) {
  const cfg = workflowStatusConfig[status]
  return (
    <span className={cn('inline-flex items-center gap-1.5 rounded-full border px-2.5 py-0.5 text-xs font-medium', cfg.classes, className)}>
      <span className={cn('w-1.5 h-1.5 rounded-full shrink-0', cfg.dot)} />
      {cfg.label}
    </span>
  )
}

// ── Finding severity badge ─────────────────────────────────────────────────

const severityConfig: Record<FindingSeverity, { label: string; classes: string }> = {
  critical: { label: 'Critical', classes: 'bg-error/10 text-error border-error/20' },
  high:     { label: 'High',     classes: 'bg-orange-500/10 text-orange-500 border-orange-500/20' },
  medium:   { label: 'Medium',   classes: 'bg-warning/10 text-warning border-warning/20' },
  low:      { label: 'Low',      classes: 'bg-info/10 text-info border-info/20' },
  info:     { label: 'Info',     classes: 'bg-muted text-muted-foreground border-border' },
}

interface SeverityBadgeProps {
  severity: FindingSeverity
  className?: string
}

export function SeverityBadge({ severity, className }: SeverityBadgeProps) {
  const cfg = severityConfig[severity] ?? severityConfig.info
  return (
    <span className={cn('inline-flex items-center rounded-full border px-2.5 py-0.5 text-xs font-semibold uppercase tracking-wide', cfg.classes, className)}>
      {cfg.label}
    </span>
  )
}

// ── Finding status badge ───────────────────────────────────────────────────

const findingStatusConfig: Record<FindingStatus, { label: string; classes: string }> = {
  open:                 { label: 'Open',                classes: 'bg-error/10 text-error border-error/20' },
  in_review:            { label: 'In Review',           classes: 'bg-info/10 text-info border-info/20' },
  approved:             { label: 'Approved',            classes: 'bg-success/10 text-success border-success/20' },
  rejected:             { label: 'Rejected',            classes: 'bg-muted text-muted-foreground border-border' },
  pending_fix:          { label: 'Pending Fix',         classes: 'bg-warning/10 text-warning border-warning/20' },
  fixed:                { label: 'Fixed',               classes: 'bg-success/10 text-success border-success/20' },
  verified:             { label: 'Verified',            classes: 'bg-success/10 text-success border-success/20' },
  verification_failed:  { label: 'Verification Failed', classes: 'bg-error/10 text-error border-error/20' },
  dismissed:            { label: 'Dismissed',           classes: 'bg-muted text-muted-foreground border-border' },
}

interface FindingStatusBadgeProps {
  status: FindingStatus
  className?: string
}

export function FindingStatusBadge({ status, className }: FindingStatusBadgeProps) {
  const cfg = findingStatusConfig[status] ?? findingStatusConfig.open
  return (
    <span className={cn('inline-flex items-center rounded-full border px-2.5 py-0.5 text-xs font-medium', cfg.classes, className)}>
      {cfg.label}
    </span>
  )
}
