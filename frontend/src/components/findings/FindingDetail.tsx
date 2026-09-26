import type { Finding } from '@/types/finding'
import { SeverityBadge, FindingStatusBadge } from '@/components/ui/status-badge'
import { Button } from '@/components/ui/button'
import { X, FileCode2, AlertCircle, Lightbulb, CheckCircle2, ShieldAlert } from 'lucide-react'
import { Separator } from '@/components/ui/separator'

const agentLabel: Record<string, string> = {
  code_review:    'Code Review Agent',
  security:       'Security Agent',
  test_analysis:  'Test Analysis Agent',
  documentation:  'Documentation Agent',
}

interface FindingDetailProps {
  finding: Finding
  onClose?: () => void
  onApprove?: () => void
  onReject?: () => void
}

export function FindingDetail({ finding, onClose, onApprove, onReject }: FindingDetailProps) {
  const hasFixProposal = !!finding.fixProposal || finding.status === 'open'

  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <div className="flex items-start justify-between gap-3 p-5 border-b border-border">
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 flex-wrap mb-1">
            <SeverityBadge severity={finding.severity} />
            <FindingStatusBadge status={finding.status} />
          </div>
          <h3 className="text-sm font-semibold text-foreground mt-2">{finding.title}</h3>
          <p className="text-xs text-muted-foreground mt-0.5">{agentLabel[finding.agent] ?? finding.agent}</p>
        </div>
        {onClose && (
          <Button variant="ghost" size="icon" onClick={onClose} className="shrink-0 text-muted-foreground">
            <X className="w-4 h-4" />
          </Button>
        )}
      </div>

      {/* Scrollable body */}
      <div className="flex-1 overflow-y-auto scrollbar-thin p-5 space-y-5">
        {/* Description */}
        <Section icon={AlertCircle} title="Description">
          <p className="text-sm text-foreground leading-relaxed">{finding.description}</p>
        </Section>

        {/* Location */}
        <Section icon={FileCode2} title="Location">
          <code className="text-xs font-mono bg-muted px-2 py-1 rounded text-foreground">
            {finding.location.file}{finding.location.line != null ? `:${finding.location.line}` : ''}
          </code>
        </Section>

        {/* Evidence */}
        {finding.evidence && (
          <Section icon={ShieldAlert} title="Evidence">
            <pre className="text-xs font-mono bg-muted text-foreground p-3 rounded-md overflow-x-auto whitespace-pre-wrap break-all">
              {finding.evidence}
            </pre>
          </Section>
        )}

        {/* Why it matters */}
        {finding.whyItMatters && (
          <Section icon={AlertCircle} title="Why it matters">
            <p className="text-sm text-foreground leading-relaxed">{finding.whyItMatters}</p>
          </Section>
        )}

        {/* Suggested fix */}
        {finding.suggestedFix && (
          <Section icon={Lightbulb} title="Suggested fix">
            <p className="text-sm text-foreground leading-relaxed">{finding.suggestedFix}</p>
          </Section>
        )}

        {/* Verification */}
        {finding.verificationMethod && (
          <Section icon={CheckCircle2} title="Verification method">
            <p className="text-sm text-foreground leading-relaxed">{finding.verificationMethod}</p>
          </Section>
        )}
      </div>

      {/* Actions */}
      {hasFixProposal && finding.status === 'open' && (
        <>
          <Separator />
          <div className="p-4 flex gap-2">
            <Button
              variant="outline"
              size="sm"
              className="flex-1"
              onClick={() => onReject?.()}
            >
              Reject
            </Button>
            <Button
              size="sm"
              className="flex-1"
              onClick={() => onApprove?.()}
            >
              Approve Fix
            </Button>
          </div>
        </>
      )}
    </div>
  )
}

function Section({ icon: Icon, title, children }: { icon: React.ComponentType<{ className?: string }>; title: string; children: React.ReactNode }) {
  return (
    <div className="space-y-2">
      <div className="flex items-center gap-2">
        <Icon className="w-3.5 h-3.5 text-muted-foreground" />
        <p className="text-xs font-semibold text-muted-foreground uppercase tracking-wide">{title}</p>
      </div>
      {children}
    </div>
  )
}
