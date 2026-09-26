import { FileText } from 'lucide-react'
import { Card, CardContent } from '@/components/ui/card'

export default function Reports() {
  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-lg font-semibold text-foreground">Reports</h2>
        <p className="text-sm text-muted-foreground mt-0.5">
          Final analysis reports from completed workflow runs.
        </p>
      </div>

      <Card className="border-dashed">
        <CardContent className="flex flex-col items-center justify-center py-16 gap-3">
          <FileText className="w-10 h-10 text-muted-foreground/40" />
          <p className="text-sm font-medium text-foreground">No reports available</p>
          <p className="text-xs text-muted-foreground text-center max-w-sm">
            Complete a workflow run to generate a full analysis report with
            productivity metrics, test results, and remediation summary.
          </p>
          <p className="text-xs text-amber-500 mt-2">
            Backend integration pending — reports will be built in Phase 6.
          </p>
        </CardContent>
      </Card>
    </div>
  )
}
