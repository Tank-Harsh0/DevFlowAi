import { AlertTriangle } from 'lucide-react'
import { Card, CardContent } from '@/components/ui/card'

export default function Findings() {
  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-lg font-semibold text-foreground">Findings</h2>
        <p className="text-sm text-muted-foreground mt-0.5">
          Issues discovered by AI agents across all workflow runs.
        </p>
      </div>

      <Card className="border-dashed">
        <CardContent className="flex flex-col items-center justify-center py-16 gap-3">
          <AlertTriangle className="w-10 h-10 text-muted-foreground/40" />
          <p className="text-sm font-medium text-foreground">No findings yet</p>
          <p className="text-xs text-muted-foreground text-center max-w-sm">
            Run a workflow to detect issues. Findings will be listed here with
            severity, location, and suggested fixes.
          </p>
          <p className="text-xs text-amber-500 mt-2">
            Backend integration pending — findings will be built in Phase 5.
          </p>
        </CardContent>
      </Card>
    </div>
  )
}
