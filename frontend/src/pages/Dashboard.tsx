import {
  LayoutDashboard,
  GitBranch,
  AlertTriangle,
  CheckCircle2,
  TestTube2,
  Clock,
} from 'lucide-react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'

const stats = [
  {
    label: 'Workflows Run',
    value: '—',
    icon: LayoutDashboard,
    description: 'Total workflow executions',
  },
  {
    label: 'Repositories',
    value: '—',
    icon: GitBranch,
    description: 'Connected repositories',
  },
  {
    label: 'Issues Found',
    value: '—',
    icon: AlertTriangle,
    description: 'Total findings detected',
  },
  {
    label: 'Issues Fixed',
    value: '—',
    icon: CheckCircle2,
    description: 'Issues resolved by AI',
  },
  {
    label: 'Tests Generated',
    value: '—',
    icon: TestTube2,
    description: 'New tests created',
  },
  {
    label: 'Time Saved',
    value: '—',
    icon: Clock,
    description: 'vs. manual workflow',
  },
]

export default function Dashboard() {
  return (
    <div className="space-y-6">
      {/* Page header */}
      <div>
        <h2 className="text-lg font-semibold text-foreground">Overview</h2>
        <p className="text-sm text-muted-foreground mt-0.5">
          Real-time metrics will appear here once the backend is connected.
        </p>
      </div>

      {/* Stats grid */}
      <div className="grid grid-cols-2 lg:grid-cols-3 gap-4">
        {stats.map(({ label, value, icon: Icon, description }) => (
          <Card key={label}>
            <CardHeader className="flex flex-row items-center justify-between pb-2">
              <CardTitle className="text-xs font-medium text-muted-foreground uppercase tracking-wide">
                {label}
              </CardTitle>
              <Icon className="w-4 h-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <p className="text-2xl font-bold text-foreground">{value}</p>
              <p className="text-xs text-muted-foreground mt-1">{description}</p>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Pending backend notice */}
      <Card className="border-dashed">
        <CardContent className="flex items-center gap-3 py-5">
          <div className="w-2 h-2 rounded-full bg-amber-500 shrink-0" />
          <p className="text-sm text-muted-foreground">
            <span className="font-medium text-foreground">Backend integration pending.</span>{' '}
            Dashboard data will be fetched from the API once the backend endpoints are available.
          </p>
        </CardContent>
      </Card>
    </div>
  )
}
