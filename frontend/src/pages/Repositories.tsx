import { GitBranch, Plus } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Card, CardContent } from '@/components/ui/card'

export default function Repositories() {
  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-lg font-semibold text-foreground">Repositories</h2>
          <p className="text-sm text-muted-foreground mt-0.5">
            Connect Git repositories to start AI-powered workflow analysis.
          </p>
        </div>
        <Button size="sm" disabled>
          <Plus className="w-4 h-4" />
          Add Repository
        </Button>
      </div>

      {/* Empty state */}
      <Card className="border-dashed">
        <CardContent className="flex flex-col items-center justify-center py-16 gap-3">
          <GitBranch className="w-10 h-10 text-muted-foreground/40" />
          <p className="text-sm font-medium text-foreground">No repositories connected</p>
          <p className="text-xs text-muted-foreground text-center max-w-sm">
            Connect a Git repository to analyze code quality, run security checks,
            and generate tests with AI agents.
          </p>
          <p className="text-xs text-amber-500 mt-2">
            Backend integration pending — repository API not yet available.
          </p>
        </CardContent>
      </Card>
    </div>
  )
}
