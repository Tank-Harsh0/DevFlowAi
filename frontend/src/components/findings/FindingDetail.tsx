/**
 * FindingDetail — the right-panel detail view for a selected finding.
 *
 * Sections:
 *  - Header: severity, status, agent
 *  - Description
 *  - Code location (file, line, function)
 *  - Code snippet (if provided by backend)
 *  - Evidence
 *  - Why it matters
 *  - AI analysis / suggested fix
 *  - Fix proposal (diff + affected files)
 *  - Verification status
 *  - Actions (Approve / Reject)
 *
 * Human approval is explicit — the developer must confirm via a modal dialog
 * before any action is sent to the backend.
 */

import { useState } from 'react'
import {
  X, FileCode2, AlertCircle, Lightbulb, CheckCircle2, ShieldAlert,
  GitMerge, Layers, ArrowLeft, ArrowRight, Link2,
} from 'lucide-react'
import { Link } from 'react-router-dom'
import { Button } from '@/components/ui/button'
import { Separator } from '@/components/ui/separator'
import { SeverityBadge, FindingStatusBadge } from '@/components/ui/status-badge'
import { CodeViewer } from '@/components/findings/CodeViewer'
import { DiffViewer } from '@/components/findings/DiffViewer'
import { VerificationStatus } from '@/components/findings/VerificationStatus'
import { ApproveDialog, RejectDialog } from '@/components/findings/ApprovalDialog'
import type { Finding } from '@/types/finding'

// ── Helpers ───────────────────────────────────────────────────────────────────

const AGENT_LABEL: Record<string, string> = {
  code_review:    'Code Review Agent',
  security:       'Security Agent',
  test_analysis:  'Test Analysis Agent',
  documentation:  'Documentation Agent',
}

function formatDate(iso: string): string {
  return new Date(iso).toLocaleString('en-US', {
    month: 'short', day: 'numeric', year: 'numeric',
    hour: '2-digit', minute: '2-digit',
  })
}

// ── Section wrapper ───────────────────────────────────────────────────────────

function Section({
  icon: Icon,
  title,
  children,
}: {
  icon: React.ComponentType<{ className?: string }>
  title: string
  children: React.ReactNode
}) {
  return (
    <div className="space-y-2">
      <div className="flex items-center gap-2">
        <Icon className="w-3.5 h-3.5 text-muted-foreground shrink-0" />
        <p className="text-xs font-semibold text-muted-foreground uppercase tracking-wide">
          {title}
        </p>
      </div>
      {children}
    </div>
  )
}

// ── Approval action bar ───────────────────────────────────────────────────────

interface ActionBarProps {
  finding: Finding
  onApprove: () => void
  onReject: () => void
  submitting: boolean
}

function ActionBar({ finding, onApprove, onReject, submitting }: ActionBarProps) {
  const canApprove =
    finding.status === 'open' || finding.status === 'in_review'

  if (!canApprove || !finding.fixProposal) return null

  return (
    <>
      <Separator />
      <div className="p-4 space-y-3">
        <div className="flex items-start gap-2 p-2.5 rounded-md bg-info/8 border border-info/20">
          <AlertCircle className="w-4 h-4 text-info shrink-0 mt-0.5" />
          <p className="text-xs text-info leading-snug">
            <strong>AI fix requires your approval.</strong> Review the proposed change above before deciding.
          </p>
        </div>
        <div className="flex gap-2">
          <Button
            variant="outline"
            size="sm"
            className="flex-1 border-error/30 text-error hover:bg-error/5 hover:text-error"
            onClick={onReject}
            disabled={submitting}
            aria-label="Reject this fix proposal"
          >
            Reject Fix
          </Button>
          <Button
            size="sm"
            className="flex-1"
            onClick={onApprove}
            disabled={submitting}
            aria-label="Approve this fix proposal"
          >
            Approve Fix
          </Button>
        </div>
      </div>
    </>
  )
}

// ── Main component ────────────────────────────────────────────────────────────

interface FindingDetailProps {
  finding: Finding
  /** Index within the current filtered list (0-based) */
  index?: number
  total?: number
  onClose?: () => void
  onPrev?: () => void
  onNext?: () => void
  /** Called after backend confirms approval/rejection (no arg — caller should refetch) */
  onApproved?: () => void
  onRejected?: () => void
}

export function FindingDetail({
  finding,
  index,
  total,
  onClose,
  onPrev,
  onNext,
  onApproved,
  onRejected,
}: FindingDetailProps) {
  const [showApproveDialog, setShowApproveDialog] = useState(false)
  const [showRejectDialog, setShowRejectDialog] = useState(false)
  const [submitting, setSubmitting] = useState(false)
  const [actionError, setActionError] = useState<string | null>(null)

  const proposal = finding.fixProposal
  const hasNavigation = total !== undefined && total > 1

  // ── Approval handler ──────────────────────────────────────────────────────

  async function handleApprove() {
    if (!proposal) return
    setSubmitting(true)
    setActionError(null)
    try {
      const { findingsService } = await import('@/services/findings')
      await findingsService.approveFix(finding.id)
      setShowApproveDialog(false)
      onApproved?.()
    } catch (err) {
      setActionError(err instanceof Error ? err.message : 'Approval request failed.')
    } finally {
      setSubmitting(false)
    }
  }

  async function handleReject(reason?: string) {
    if (!proposal) return
    setSubmitting(true)
    setActionError(null)
    try {
      const { findingsService } = await import('@/services/findings')
      await findingsService.rejectFix(finding.id, reason)
      setShowRejectDialog(false)
      onRejected?.()
    } catch (err) {
      setActionError(err instanceof Error ? err.message : 'Rejection request failed.')
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <>
      <div className="flex flex-col h-full">
        {/* ── Header ── */}
        <div className="flex items-start justify-between gap-3 p-5 border-b border-border shrink-0">
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2 flex-wrap">
              <SeverityBadge severity={finding.severity} />
              <FindingStatusBadge status={finding.status} />
              <span className="text-[10px] text-muted-foreground ml-auto">
                {AGENT_LABEL[finding.agent] ?? finding.agent}
              </span>
            </div>
            <h3 className="text-sm font-semibold text-foreground mt-2 leading-snug">
              {finding.title}
            </h3>
            <p className="text-[10px] text-muted-foreground mt-1">
              Created {formatDate(finding.createdAt)}
            </p>
          </div>

          {/* Close + navigation */}
          <div className="flex items-center gap-1 shrink-0">
            {hasNavigation && (
              <>
                <Button
                  variant="ghost"
                  size="icon"
                  onClick={onPrev}
                  disabled={index === 0}
                  aria-label="Previous finding"
                  className="text-muted-foreground w-7 h-7"
                >
                  <ArrowLeft className="w-3.5 h-3.5" />
                </Button>
                <span className="text-[10px] text-muted-foreground tabular-nums w-10 text-center">
                  {(index ?? 0) + 1}/{total}
                </span>
                <Button
                  variant="ghost"
                  size="icon"
                  onClick={onNext}
                  disabled={index === (total ?? 1) - 1}
                  aria-label="Next finding"
                  className="text-muted-foreground w-7 h-7"
                >
                  <ArrowRight className="w-3.5 h-3.5" />
                </Button>
              </>
            )}
            {onClose && (
              <Button
                variant="ghost"
                size="icon"
                onClick={onClose}
                className="text-muted-foreground w-7 h-7"
                aria-label="Close finding detail"
              >
                <X className="w-4 h-4" />
              </Button>
            )}
          </div>
        </div>

        {/* ── Scrollable body ── */}
        <div className="flex-1 overflow-y-auto scrollbar-thin p-5 space-y-5 min-h-0">

          {/* Action error */}
          {actionError && (
            <div className="flex items-start gap-2 p-3 rounded-md bg-error/8 border border-error/20">
              <AlertCircle className="w-4 h-4 text-error shrink-0 mt-0.5" />
              <p className="text-xs text-error">{actionError}</p>
            </div>
          )}

          {/* Verification status (when fix is in progress or done) */}
          {(finding.status === 'approved' ||
            finding.status === 'pending_fix' ||
            finding.status === 'fixed' ||
            finding.status === 'verified' ||
            finding.status === 'verification_failed') && (
            <VerificationStatus status={finding.status} />
          )}

          {/* Description */}
          <Section icon={AlertCircle} title="Description">
            <p className="text-sm text-foreground leading-relaxed">{finding.description}</p>
          </Section>

          {/* Code location */}
          <Section icon={FileCode2} title="Location">
            <div className="space-y-1.5">
              <code className="block text-xs font-mono bg-muted px-3 py-1.5 rounded text-foreground">
                {finding.location.file}
                {finding.location.line != null && `:${finding.location.line}`}
                {finding.location.endLine != null && `-${finding.location.endLine}`}
              </code>
              {finding.location.function && (
                <p className="text-xs text-muted-foreground">
                  Function: <code className="font-mono text-foreground">{finding.location.function}</code>
                </p>
              )}
            </div>
          </Section>

          {/* Code snippet from backend */}
          {finding.codeSnippet ? (
            <Section icon={FileCode2} title="Source context">
              <CodeViewer
                content={finding.codeSnippet.content}
                startLine={finding.codeSnippet.startLine}
                highlightLines={finding.codeSnippet.highlightLines}
                language={finding.codeSnippet.language}
              />
            </Section>
          ) : finding.evidence ? (
            /* Fallback: raw evidence string */
            <Section icon={ShieldAlert} title="Evidence">
              <pre className="text-xs font-mono bg-muted text-foreground p-3 rounded-md overflow-x-auto whitespace-pre-wrap scrollbar-thin border border-border">
                {finding.evidence}
              </pre>
            </Section>
          ) : null}

          {/* Why it matters */}
          {finding.whyItMatters && (
            <Section icon={AlertCircle} title="Why it matters">
              <p className="text-sm text-foreground leading-relaxed">{finding.whyItMatters}</p>
            </Section>
          )}

          {/* Suggested fix (text) */}
          {finding.suggestedFix && (
            <Section icon={Lightbulb} title="Suggested fix">
              <p className="text-sm text-foreground leading-relaxed">{finding.suggestedFix}</p>
            </Section>
          )}

          {/* Fix proposal */}
          {proposal && (
            <>
              <Separator />
              <Section icon={GitMerge} title="Proposed fix">
                <div className="space-y-3">
                  <p className="text-sm text-foreground leading-relaxed">{proposal.description}</p>

                  {/* Reason */}
                  <div className="p-2.5 rounded-md bg-muted border border-border">
                    <p className="text-[10px] font-semibold text-muted-foreground uppercase tracking-wide mb-1">
                      Reason
                    </p>
                    <p className="text-xs text-foreground">{proposal.reason}</p>
                  </div>

                  {/* Risk + affected files */}
                  <div className="flex items-center gap-3 flex-wrap">
                    <div>
                      <p className="text-[10px] font-semibold text-muted-foreground uppercase tracking-wide mb-0.5">
                        Risk
                      </p>
                      <span className={`text-xs font-semibold capitalize ${
                        proposal.risk === 'high' ? 'text-error' :
                        proposal.risk === 'medium' ? 'text-warning' : 'text-success'
                      }`}>
                        {proposal.risk}
                      </span>
                    </div>
                    {proposal.affectedFiles.length > 0 && (
                      <div>
                        <p className="text-[10px] font-semibold text-muted-foreground uppercase tracking-wide mb-0.5">
                          Affected files
                        </p>
                        <div className="flex flex-wrap gap-1">
                          {proposal.affectedFiles.map((f) => (
                            <code key={f} className="text-[10px] font-mono bg-muted px-1.5 py-0.5 rounded text-foreground">
                              {f}
                            </code>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>

                  {/* Diff */}
                  {proposal.diff ? (
                    <div>
                      <p className="text-[10px] font-semibold text-muted-foreground uppercase tracking-wide mb-1.5">
                        Change
                      </p>
                      <DiffViewer diff={proposal.diff} />
                    </div>
                  ) : (
                    <p className="text-xs text-muted-foreground italic">
                      No proposed diff is available for this finding.
                    </p>
                  )}

                  {/* Rejection reason (if rejected) */}
                  {finding.status === 'rejected' && proposal.rejectionReason && (
                    <div className="p-2.5 rounded-md bg-muted border border-border">
                      <p className="text-[10px] font-semibold text-muted-foreground uppercase tracking-wide mb-1">
                        Rejection reason
                      </p>
                      <p className="text-xs text-foreground">{proposal.rejectionReason}</p>
                    </div>
                  )}
                </div>
              </Section>
            </>
          )}

          {/* Verification method */}
          {finding.verificationMethod && (
            <Section icon={CheckCircle2} title="Verification method">
              <p className="text-sm text-foreground leading-relaxed">{finding.verificationMethod}</p>
            </Section>
          )}

          {/* Workflow link */}
          <Section icon={Layers} title="Workflow">
            <div className="flex items-center gap-2 flex-wrap">
              <Link
                to={finding.workflowId ? `/workflow?workflowId=${finding.workflowId}` : '/workflow'}
                className="text-xs text-primary hover:underline flex items-center gap-1"
                aria-label="View workflow"
              >
                <Link2 className="w-3 h-3" />
                View workflow
              </Link>
            </div>
          </Section>
        </div>

        {/* ── Action bar ── */}
        <ActionBar
          finding={finding}
          onApprove={() => setShowApproveDialog(true)}
          onReject={() => setShowRejectDialog(true)}
          submitting={submitting}
        />
      </div>

      {/* ── Approve dialog ── */}
      {showApproveDialog && proposal && (
        <ApproveDialog
          proposal={proposal}
          onConfirm={() => void handleApprove()}
          onCancel={() => setShowApproveDialog(false)}
          submitting={submitting}
        />
      )}

      {/* ── Reject dialog ── */}
      {showRejectDialog && proposal && (
        <RejectDialog
          proposal={proposal}
          onConfirm={(reason) => void handleReject(reason)}
          onCancel={() => setShowRejectDialog(false)}
          submitting={submitting}
        />
      )}
    </>
  )
}
