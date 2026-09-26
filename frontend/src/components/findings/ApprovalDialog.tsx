/**
 * ApprovalDialog — modal dialogs for approving or rejecting a fix proposal.
 *
 * Both dialogs show a confirmation step before the action is sent to the backend.
 * The frontend NEVER claims the fix was applied until the backend confirms success.
 *
 * Accessibility:
 * - role="dialog" with aria-modal and aria-labelledby
 * - Focus trapped on open; Escape closes
 * - Background scroll locked while open
 */

import { useEffect, useRef, useState } from 'react'
import { AlertTriangle, CheckCircle2, XCircle } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { cn } from '@/lib/utils'
import type { FixProposal } from '@/types/finding'

// ── Shared modal shell ────────────────────────────────────────────────────────

interface DialogShellProps {
  titleId: string
  onClose: () => void
  children: React.ReactNode
}

function DialogShell({ titleId, onClose, children }: DialogShellProps) {
  const overlayRef = useRef<HTMLDivElement>(null)

  // Close on Escape
  useEffect(() => {
    function onKey(e: KeyboardEvent) {
      if (e.key === 'Escape') onClose()
    }
    document.addEventListener('keydown', onKey)
    return () => document.removeEventListener('keydown', onKey)
  }, [onClose])

  // Lock body scroll
  useEffect(() => {
    const prev = document.body.style.overflow
    document.body.style.overflow = 'hidden'
    return () => { document.body.style.overflow = prev }
  }, [])

  return (
    <div
      ref={overlayRef}
      className="fixed inset-0 z-50 flex items-center justify-center p-4"
      onClick={(e) => { if (e.target === overlayRef.current) onClose() }}
    >
      {/* Backdrop */}
      <div className="absolute inset-0 bg-background/80 backdrop-blur-sm" aria-hidden="true" />

      {/* Panel */}
      <div
        role="dialog"
        aria-modal="true"
        aria-labelledby={titleId}
        className="relative z-10 w-full max-w-md rounded-lg border border-border bg-card shadow-xl p-6 flex flex-col gap-4"
      >
        {children}
      </div>
    </div>
  )
}

// ── Risk badge ────────────────────────────────────────────────────────────────

function RiskBadge({ risk }: { risk: FixProposal['risk'] }) {
  const cfg = {
    low:    { label: 'Low risk',    classes: 'text-success bg-success/10 border-success/20' },
    medium: { label: 'Medium risk', classes: 'text-warning bg-warning/10 border-warning/20' },
    high:   { label: 'High risk',   classes: 'text-error bg-error/10 border-error/20' },
  }[risk]

  return (
    <span className={cn('inline-flex items-center rounded-full border px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wide', cfg.classes)}>
      {cfg.label}
    </span>
  )
}

// ── Approve dialog ────────────────────────────────────────────────────────────

interface ApproveDialogProps {
  proposal: FixProposal
  onConfirm: () => void
  onCancel: () => void
  submitting?: boolean
}

export function ApproveDialog({ proposal, onConfirm, onCancel, submitting }: ApproveDialogProps) {
  const titleId = 'approve-dialog-title'
  // Auto-focus the Cancel button (safer default)
  const cancelRef = useRef<HTMLButtonElement>(null)
  useEffect(() => { cancelRef.current?.focus() }, [])

  return (
    <DialogShell titleId={titleId} onClose={onCancel}>
      {/* Header */}
      <div className="flex items-start gap-3">
        <div className="flex items-center justify-center w-9 h-9 rounded-full bg-success/15 border border-success/30 shrink-0">
          <CheckCircle2 className="w-5 h-5 text-success" />
        </div>
        <div>
          <h2 id={titleId} className="text-sm font-semibold text-foreground">
            Approve AI fix?
          </h2>
          <p className="text-xs text-muted-foreground mt-1 leading-relaxed">
            This will send the proposed fix to the backend for execution. The change
            will not appear as applied until the backend confirms success.
          </p>
        </div>
      </div>

      {/* Proposal summary */}
      <div className="rounded-md bg-muted border border-border p-3 space-y-1.5">
        <p className="text-xs font-medium text-foreground">{proposal.description}</p>
        <p className="text-[10px] text-muted-foreground leading-snug">{proposal.reason}</p>
        <div className="flex items-center gap-2 pt-0.5">
          <RiskBadge risk={proposal.risk} />
          {proposal.affectedFiles.length > 0 && (
            <span className="text-[10px] text-muted-foreground">
              {proposal.affectedFiles.length} file{proposal.affectedFiles.length !== 1 ? 's' : ''} affected
            </span>
          )}
        </div>
      </div>

      {/* Risk warning for high-risk fixes */}
      {proposal.risk === 'high' && (
        <div className="flex items-start gap-2 p-2.5 rounded-md bg-error/8 border border-error/20">
          <AlertTriangle className="w-4 h-4 text-error shrink-0 mt-0.5" />
          <p className="text-xs text-error leading-snug">
            This fix is classified as <strong>high risk</strong>. Review the diff carefully before approving.
          </p>
        </div>
      )}

      {/* Actions */}
      <div className="flex gap-2 justify-end pt-1">
        <Button
          ref={cancelRef}
          variant="outline"
          size="sm"
          onClick={onCancel}
          disabled={submitting}
        >
          Cancel
        </Button>
        <Button
          size="sm"
          onClick={onConfirm}
          disabled={submitting}
          className="gap-1.5"
        >
          {submitting ? (
            <>Approving…</>
          ) : (
            <><CheckCircle2 className="w-3.5 h-3.5" /> Approve Fix</>
          )}
        </Button>
      </div>
    </DialogShell>
  )
}

// ── Reject dialog ─────────────────────────────────────────────────────────────

interface RejectDialogProps {
  proposal: FixProposal
  onConfirm: (reason?: string) => void
  onCancel: () => void
  submitting?: boolean
}

export function RejectDialog({ proposal, onConfirm, onCancel, submitting }: RejectDialogProps) {
  const titleId = 'reject-dialog-title'
  const [reason, setReason] = useState('')
  const cancelRef = useRef<HTMLButtonElement>(null)
  useEffect(() => { cancelRef.current?.focus() }, [])

  return (
    <DialogShell titleId={titleId} onClose={onCancel}>
      {/* Header */}
      <div className="flex items-start gap-3">
        <div className="flex items-center justify-center w-9 h-9 rounded-full bg-muted border border-border shrink-0">
          <XCircle className="w-5 h-5 text-muted-foreground" />
        </div>
        <div>
          <h2 id={titleId} className="text-sm font-semibold text-foreground">
            Reject AI fix
          </h2>
          <p className="text-xs text-muted-foreground mt-1 leading-relaxed">
            Rejecting will keep the finding open. No code changes will be made.
          </p>
        </div>
      </div>

      {/* Proposal name */}
      <p className="text-xs text-muted-foreground">
        Fix: <span className="text-foreground font-medium">{proposal.description}</span>
      </p>

      {/* Optional reason input */}
      <div className="space-y-1.5">
        <label
          htmlFor="rejection-reason"
          className="text-xs font-medium text-muted-foreground"
        >
          Reason <span className="text-muted-foreground/60 font-normal">(optional)</span>
        </label>
        <textarea
          id="rejection-reason"
          value={reason}
          onChange={(e) => setReason(e.target.value)}
          placeholder="e.g. The proposed approach conflicts with our architecture..."
          rows={3}
          className="w-full text-sm rounded-md border border-border bg-background px-3 py-2 text-foreground placeholder:text-muted-foreground/60 focus:outline-none focus:ring-2 focus:ring-ring resize-none"
          disabled={submitting}
        />
      </div>

      {/* Actions */}
      <div className="flex gap-2 justify-end pt-1">
        <Button
          ref={cancelRef}
          variant="outline"
          size="sm"
          onClick={onCancel}
          disabled={submitting}
        >
          Cancel
        </Button>
        <Button
          variant="outline"
          size="sm"
          onClick={() => onConfirm(reason.trim() || undefined)}
          disabled={submitting}
          className="gap-1.5 border-error/30 text-error hover:bg-error/5 hover:text-error"
        >
          {submitting ? (
            <>Rejecting…</>
          ) : (
            <><XCircle className="w-3.5 h-3.5" /> Reject Fix</>
          )}
        </Button>
      </div>
    </DialogShell>
  )
}
