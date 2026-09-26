import { XCircle, RefreshCw } from 'lucide-react'
import { Button } from '@/components/ui/button'

interface WorkflowErrorProps {
  failedStep?: string
  errorMessage?: string
  onRetry?: () => void
}

export function WorkflowError({ failedStep, errorMessage, onRetry }: WorkflowErrorProps) {
  return (
    <div className="rounded-lg border border-error/30 bg-error/5 p-4">
      <div className="flex items-start gap-3">
        <div className="flex items-center justify-center w-8 h-8 rounded-full bg-error/15 border border-error/30 shrink-0">
          <XCircle className="w-4 h-4 text-error" />
        </div>
        <div className="flex-1 min-w-0">
          <p className="text-sm font-semibold text-foreground">Workflow failed</p>
          {failedStep && (
            <p className="text-xs text-muted-foreground mt-0.5">
              <span className="font-medium text-error">{failedStep}</span> encountered an error.
            </p>
          )}
          {errorMessage && (
            <p className="text-xs text-muted-foreground mt-1 font-mono bg-muted px-2 py-1 rounded">
              {errorMessage}
            </p>
          )}
        </div>
      </div>
      {onRetry && (
        <div className="mt-3 ml-11">
          <Button size="sm" variant="outline" onClick={onRetry}>
            <RefreshCw className="w-3.5 h-3.5" />
            Retry Workflow
          </Button>
        </div>
      )}
    </div>
  )
}
