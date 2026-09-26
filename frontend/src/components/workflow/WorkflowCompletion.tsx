import { CheckCircle2, ArrowRight } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Link } from 'react-router-dom'
import type { WorkflowRun } from '@/types/workflow'

interface WorkflowCompletionProps {
  workflow: WorkflowRun
}

export function WorkflowCompletion({ workflow }: WorkflowCompletionProps) {
  return (
    <div className="rounded-lg border border-success/30 bg-success/5 p-4">
      <div className="flex items-start gap-3">
        <div className="flex items-center justify-center w-8 h-8 rounded-full bg-success/15 border border-success/30 shrink-0">
          <CheckCircle2 className="w-4 h-4 text-success" />
        </div>
        <div className="flex-1 min-w-0">
          <p className="text-sm font-semibold text-foreground">Workflow completed</p>
          <div className="flex flex-wrap gap-x-4 gap-y-0.5 mt-1">
            {workflow.totalFindings !== undefined && (
              <span className="text-xs text-muted-foreground">
                <span className="font-medium text-foreground">{workflow.totalFindings}</span> findings
              </span>
            )}
            {workflow.fixedFindings !== undefined && (
              <span className="text-xs text-muted-foreground">
                <span className="font-medium text-success">{workflow.fixedFindings}</span> fixed
              </span>
            )}
            {workflow.testsPassed !== undefined && (
              <span className="text-xs text-muted-foreground">
                <span className="font-medium text-success">{workflow.testsPassed}</span> tests passed
              </span>
            )}
          </div>
        </div>
      </div>
      <div className="flex gap-2 mt-3 ml-11">
        <Button size="sm" variant="outline" asChild>
          <Link to={`/findings?workflowId=${workflow.id}`}>
            View Findings <ArrowRight className="w-3.5 h-3.5" />
          </Link>
        </Button>
        <Button size="sm" variant="outline" asChild>
          <Link to="/reports">
            View Report <ArrowRight className="w-3.5 h-3.5" />
          </Link>
        </Button>
      </div>
    </div>
  )
}
