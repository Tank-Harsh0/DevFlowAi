import type { Finding } from '@/types/finding'
import { SeverityBadge, FindingStatusBadge } from '@/components/ui/status-badge'
import { cn } from '@/lib/utils'

const agentLabel: Record<string, string> = {
  code_review:    'Code Review',
  security:       'Security',
  test_analysis:  'Test Analysis',
  documentation:  'Documentation',
}

interface FindingRowProps {
  finding: Finding
  selected?: boolean
  onClick?: () => void
}

export function FindingRow({ finding, selected, onClick }: FindingRowProps) {
  return (
    <button
      type="button"
      onClick={onClick}
      className={cn(
        'w-full text-left px-4 py-3.5 flex items-start gap-3 hover:bg-accent transition-colors border-b border-border last:border-b-0',
        selected && 'bg-primary/5 border-l-2 border-l-primary'
      )}
    >
      <div className="pt-0.5">
        <SeverityBadge severity={finding.severity} />
      </div>
      <div className="flex-1 min-w-0">
        <p className="text-sm font-medium text-foreground truncate">{finding.title}</p>
        <p className="text-xs text-muted-foreground mt-0.5 truncate">{finding.description}</p>
        <div className="flex items-center gap-3 mt-1.5">
          <span className="text-xs text-muted-foreground font-mono">
            {finding.location.file}{finding.location.line != null ? `:${finding.location.line}` : ''}
          </span>
          <span className="text-xs text-muted-foreground">{agentLabel[finding.agent] ?? finding.agent}</span>
        </div>
      </div>
      <div className="shrink-0 pt-0.5">
        <FindingStatusBadge status={finding.status} />
      </div>
    </button>
  )
}
