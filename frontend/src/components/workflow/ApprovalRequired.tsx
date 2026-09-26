import { UserCheck, ArrowRight } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Link } from 'react-router-dom'

interface ApprovalRequiredProps {
  stepLabel?: string
  message?: string
  /** When provided, the "Review Changes" button links to findings filtered by this workflow */
  workflowId?: string
}

export function ApprovalRequired({ stepLabel, message, workflowId }: ApprovalRequiredProps) {
  const findingsHref = workflowId ? `/findings?workflowId=${workflowId}` : '/findings'

  return (
    <div className="rounded-lg border border-info/30 bg-info/5 p-4">
      <div className="flex items-start gap-3">
        <div className="flex items-center justify-center w-8 h-8 rounded-full bg-info/15 border border-info/30 shrink-0">
          <UserCheck className="w-4 h-4 text-info" />
        </div>
        <div className="flex-1 min-w-0">
          <p className="text-sm font-semibold text-foreground">Human approval required</p>
          <p className="text-xs text-muted-foreground mt-0.5">
            {message ??
              (stepLabel
                ? `The ${stepLabel} step is waiting for developer review before continuing.`
                : 'The AI has proposed changes that require developer review before continuing.')}
          </p>
        </div>
      </div>
      <div className="flex gap-2 mt-3 ml-11">
        <Button size="sm" variant="outline" asChild>
          <Link to={findingsHref}>
            Review Changes <ArrowRight className="w-3.5 h-3.5" />
          </Link>
        </Button>
      </div>
    </div>
  )
}
