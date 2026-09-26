/**
 * VerificationStatus — shows the verification state of a finding after
 * an approved fix has been applied.
 *
 * Only shows states that the backend explicitly provides.
 * Never synthesises a "verified" state without backend confirmation.
 */

import { CheckCircle2, XCircle, Loader2 } from 'lucide-react'
import type { FindingStatus } from '@/types/finding'
import { cn } from '@/lib/utils'

interface VerificationStatusProps {
  status: FindingStatus
  className?: string
}

export function VerificationStatus({ status, className }: VerificationStatusProps) {
  if (status === 'pending_fix' || status === 'approved') {
    return (
      <div className={cn('flex items-center gap-2 p-3 rounded-md bg-warning/8 border border-warning/20', className)}>
        <Loader2 className="w-4 h-4 text-warning animate-spin shrink-0" />
        <div>
          <p className="text-xs font-semibold text-warning">Fix in progress</p>
          <p className="text-[10px] text-muted-foreground mt-0.5">
            The approved fix is being applied. Verification will run automatically.
          </p>
        </div>
      </div>
    )
  }

  if (status === 'fixed') {
    return (
      <div className={cn('flex items-center gap-2 p-3 rounded-md bg-info/8 border border-info/20', className)}>
        <Loader2 className="w-4 h-4 text-info animate-spin shrink-0" />
        <div>
          <p className="text-xs font-semibold text-info">Verifying fix</p>
          <p className="text-[10px] text-muted-foreground mt-0.5">
            Running verification tests against the applied fix…
          </p>
        </div>
      </div>
    )
  }

  if (status === 'verified') {
    return (
      <div className={cn('flex items-center gap-2 p-3 rounded-md bg-success/8 border border-success/20', className)}>
        <CheckCircle2 className="w-4 h-4 text-success shrink-0" />
        <div>
          <p className="text-xs font-semibold text-success">Verification passed</p>
          <p className="text-[10px] text-muted-foreground mt-0.5">
            The fix was applied and all verification tests passed.
          </p>
        </div>
      </div>
    )
  }

  if (status === 'verification_failed') {
    return (
      <div className={cn('flex items-center gap-2 p-3 rounded-md bg-error/8 border border-error/20', className)}>
        <XCircle className="w-4 h-4 text-error shrink-0" />
        <div>
          <p className="text-xs font-semibold text-error">Verification failed</p>
          <p className="text-[10px] text-muted-foreground mt-0.5">
            The verification tests did not pass after the fix was applied.
          </p>
        </div>
      </div>
    )
  }

  return null
}
