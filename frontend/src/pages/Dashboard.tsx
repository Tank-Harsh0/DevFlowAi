import { Link } from 'react-router-dom'
import {
  Activity,
  AlertTriangle,
  CheckCircle2,
  TestTube2,
  Clock,
  ArrowRight,
  Workflow,
} from 'lucide-react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { StatCard } from '@/components/ui/stat-card'
import { WorkflowStatusBadge } from '@/components/ui/status-badge'
import { MockDataNotice } from '@/components/ui/mock-notice'
import { AgentActivityFeed } from '@/components/workflow/AgentActivityFeed'
import { useWorkflows } from '@/hooks/useWorkflows'
import { useFindings } from '@/hooks/useFindings'

function formatDuration(startIso: string, endIso?: string): string {
  const start = new Date(startIso).getTime()
  const end = endIso ? new Date(endIso).getTime() : Date.now()
  const secs = Math.floor((end - start) / 1000)
  if (secs < 60) return `${secs}s`
  const mins = Math.floor(secs / 60)
  if (mins < 60) return `${mins}m`
  return `${Math.floor(mins / 60)}h ${mins % 60}m`
}

function formatRelativeTime(iso: string): string {
  const diff = Date.now() - new Date(iso).getTime()
  const mins = Math.floor(diff / 60000)
  if (mins < 60) return `${mins}m ago`
  const hrs = Math.floor(mins / 60)
  if (hrs < 24) return `${hrs}h ago`
  return `${Math.floor(hrs / 24)}d ago`
}

export default function Dashboard() {
  const { data: workflows, isMock: workflowsMock } = useWorkflows()
  const { data: findings, isMock: findingsMock } = useFindings()

  const isMock = workflowsMock || findingsMock
  const completedWorkflows = workflows.filter((w) => w.status === 'completed')
  const runningWorkflows = workflows.filter((w) => w.status === 'running')
  const totalFindings = findings.length
  const fixedFindings = findings.filter((f) => f.status === 'fixed').length
  const testsPassed = completedWorkflows.reduce((s, w) => s + (w.testsPassed ?? 0), 0)
  const testsGenerated = completedWorkflows.reduce((s, w) => s + (w.testsGenerated ?? 0), 0)

  // For agent activity, prefer running workflows; fall back to most recent
  const activeWorkflow =
    runningWorkflows[0] ??
    (completedWorkflows.length > 0 ? completedWorkflows[completedWorkflows.length - 1] : null) ??
    workflows[0] ??
    null

  return (
    <div className="space-y-6">
      <MockDataNotice isMock={isMock} />

      {/* Stats row */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          label="Active Workflows"
          value={runningWorkflows.length}
          icon={Activity}
          description={`${completedWorkflows.length} completed`}
        />
        <StatCard
          label="Issues Found"
          value={totalFindings}
          icon={AlertTriangle}
          description="Across all repositories"
        />
        <StatCard
          label="Issues Fixed"
          value={fixedFindings}
          icon={CheckCircle2}
          description={`${totalFindings - fixedFindings} remaining`}
        />
        <StatCard
          label="Tests Passed"
          value={testsPassed}
          icon={TestTube2}
          description={`${testsGenerated} generated`}
        />
      </div>

      {/* Two column layout */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        {/* Recent workflows */}
        <Card className="lg:col-span-2">
          <CardHeader className="flex flex-row items-center justify-between pb-3">
            <CardTitle>Recent Workflows</CardTitle>
            <Button variant="ghost" size="sm" asChild className="text-xs text-muted-foreground gap-1">
              <Link to="/workflow">
                View all <ArrowRight className="w-3 h-3" />
              </Link>
            </Button>
          </CardHeader>
          <CardContent className="p-0">
            {workflows.length === 0 ? (
              <p className="text-sm text-muted-foreground px-5 py-6">No workflow runs yet.</p>
            ) : (
              <div className="divide-y divide-border">
                {workflows.slice(0, 5).map((wf) => (
                  <div key={wf.id} className="flex items-center gap-4 px-5 py-3.5 hover:bg-accent transition-colors">
                    <div className="flex items-center justify-center w-8 h-8 rounded-md bg-primary/10 shrink-0">
                      <Workflow className="w-4 h-4 text-primary" />
                    </div>
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-medium text-foreground truncate">{wf.repositoryName}</p>
                      <div className="flex items-center gap-3 mt-0.5">
                        {wf.totalFindings !== undefined && (
                          <span className="text-xs text-muted-foreground">{wf.totalFindings} issues</span>
                        )}
                        {wf.testsPassed !== undefined && (
                          <span className="text-xs text-muted-foreground">{wf.testsPassed} tests</span>
                        )}
                        <span className="text-xs text-muted-foreground flex items-center gap-1">
                          <Clock className="w-3 h-3" />
                          {formatRelativeTime(wf.createdAt)}
                        </span>
                      </div>
                    </div>
                    <div className="flex items-center gap-3 shrink-0">
                      {wf.status === 'running' && (
                        <span className="text-xs text-muted-foreground">{formatDuration(wf.createdAt)}</span>
                      )}
                      <WorkflowStatusBadge status={wf.status} />
                    </div>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>

        {/* Agent activity */}
        <Card>
          <CardHeader className="pb-3">
            <CardTitle>Agent Activity</CardTitle>
            {activeWorkflow && (
              <p className="text-xs text-muted-foreground mt-0.5">{activeWorkflow.repositoryName}</p>
            )}
          </CardHeader>
          <CardContent className="p-0 px-4 pb-4">
            {activeWorkflow ? (
              <AgentActivityFeed steps={activeWorkflow.steps.slice(0, 8)} />
            ) : (
              <p className="text-sm text-muted-foreground py-4">No workflow activity yet.</p>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Productivity summary — derived from completed workflow data */}
      {completedWorkflows.length > 0 && (
        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-3">
            <CardTitle>Productivity Summary</CardTitle>
            <Button variant="ghost" size="sm" asChild className="text-xs text-muted-foreground gap-1">
              <Link to="/reports">
                Full report <ArrowRight className="w-3 h-3" />
              </Link>
            </Button>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-6">
              <MetricItem
                label="Tests Generated"
                value={`${testsGenerated}`}
                sub="across completed runs"
                positive
              />
              <MetricItem
                label="Issues Fixed"
                value={`${fixedFindings}`}
                sub={`of ${totalFindings} total`}
                positive={fixedFindings > 0}
              />
              <MetricItem
                label="Completed Runs"
                value={`${completedWorkflows.length}`}
                sub="workflow executions"
              />
              <MetricItem
                label="Active Now"
                value={`${runningWorkflows.length}`}
                sub="running workflows"
                positive={runningWorkflows.length > 0}
              />
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  )
}

function MetricItem({ label, value, sub, positive }: { label: string; value: string; sub: string; positive?: boolean }) {
  return (
    <div>
      <p className="text-xs font-medium text-muted-foreground uppercase tracking-wide mb-1">{label}</p>
      <p className={`text-xl font-bold tabular-nums ${positive ? 'text-success' : 'text-foreground'}`}>{value}</p>
      <p className="text-xs text-muted-foreground mt-0.5">{sub}</p>
    </div>
  )
}
