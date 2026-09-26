import type { Finding } from '@/types/finding'
import { SeverityBadge, FindingStatusBadge } from '@/components/ui/status-badge'
import { GitMerge } from 'lucide-react'
import { cn } from '@/lib/utils'

const AGENT_LABEL: Record<string, string> = {
  code_review:    'Code Review',
  security:       'Security',
  test_analysis:  'Test Analysis',
  documentation:  'Documentation',
}

function formatRelative(iso: string): string {
  const diff = Date.now() - new Date(iso).getTime()
  const mins = Math.floor(diff / 60_000)
  if (mins < 60) return `${mins}m ago`
  const hrs = Math.floor(mins / 60)
  if (hrs < 24) return `${hrs}h ago`
  return `${Math.floor(hrs / 24)}d ago`
}

interface FindingRowProps {
  finding: Finding
  selected?: boolean
  onClick?: () => void
}

export function FindingRow({ finding, selected, onClick }: FindingRowProps) {
  const hasFix = !!finding.fixProposal
  const needsApproval = finding.status === 'open' && hasFix

  return (
    <button
      type="button"
      onClick={onClick}
      aria-pressed={selected}
      className={cn(
        'w-full text-left px-4 py-3.5 flex items-start gap-3 hover:bg-accent transition-colors',
        'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-inset',
        selected
          ? 'bg-primary/5 border-l-2 border-l-primary'
          : 'border-l-2 border-l-transparent'
      )}
    >
      {/* Severity */}
      <div className="pt-0.5 shrink-0">
        <SeverityBadge severity={finding.severity} />
      </div>

      {/* Main content */}
      <div className="flex-1 min-w-0">
        <p className="text-sm font-medium text-foreground truncate">{finding.title}</p>

        <div className="flex items-center gap-2 mt-1 flex-wrap">
          <span className="text-xs text-muted-foreground font-mono">
            {finding.location.file}
            {finding.location.line != null ? `:${finding.location.line}` : ''}
          </span>
          <span className="text-muted-foreground/40 text-xs">·</span>
          <span className="text-xs text-muted-foreground">
            {AGENT_LABEL[finding.agent] ?? finding.agent}
          </span>
        </div>

        <div className="flex items-center gap-2 mt-1.5 flex-wrap">
          {/* Fix proposal indicator */}
          {needsApproval && (
            <span className="inline-flex items-center gap-1 text-[10px] font-medium text-info">
              <GitMerge className="w-2.5 h-2.5" />
              Fix available
            </span>
          )}
          <span className="text-[10px] text-muted-foreground/60 ml-auto">
            {formatRelative(finding.createdAt)}
          </span>
        </div>
      </div>

      {/* Status */}
      <div className="shrink-0 pt-0.5">
        <FindingStatusBadge status={finding.status} />
      </div>
    </button>
  )
}
