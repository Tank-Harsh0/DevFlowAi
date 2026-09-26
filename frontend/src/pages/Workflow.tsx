import { Workflow as WorkflowIcon } from 'lucide-react'
import { Card, CardContent } from '@/components/ui/card'

export default function Workflow() {
  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-lg font-semibold text-foreground">Workflow</h2>
        <p className="text-sm text-muted-foreground mt-0.5">
          Visualize and monitor the AI agent pipeline in real time.
        </p>
      </div>

      <Card className="border-dashed">
        <CardContent className="flex flex-col items-center justify-center py-16 gap-3">
          <WorkflowIcon className="w-10 h-10 text-muted-foreground/40" />
          <p className="text-sm font-medium text-foreground">No active workflow</p>
          <p className="text-xs text-muted-foreground text-center max-w-sm">
            Start a workflow from the Repositories page to see agent activity here.
          </p>
          <p className="text-xs text-amber-500 mt-2">
            Backend integration pending — workflow visualization will be built in Phase 4.
          </p>
        </CardContent>
      </Card>
    </div>
  )
}
