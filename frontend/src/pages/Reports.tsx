import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
  PieChart, Pie, Cell,
} from 'recharts'
import { FileText, Download } from 'lucide-react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { EmptyState, LoadingState, ErrorState } from '@/components/ui/states'
import { MockDataNotice } from '@/components/ui/mock-notice'
import { useReports } from '@/hooks/useReports'

const SEVERITY_COLORS: Record<string, string> = {
  Critical: 'var(--color-error)',
  High:     '#f97316',
  Medium:   'var(--color-warning)',
  Low:      'var(--color-info)',
}

function SectionTitle({ children }: { children: React.ReactNode }) {
  return (
    <h3 className="text-xs font-semibold text-muted-foreground uppercase tracking-wide mb-3">{children}</h3>
  )
}

function MetricRow({ label, value, highlight }: { label: string; value: string | number; highlight?: boolean }) {
  return (
    <div className="flex items-center justify-between py-2 border-b border-border last:border-b-0">
      <span className="text-sm text-muted-foreground">{label}</span>
      <span className={`text-sm font-semibold tabular-nums ${highlight ? 'text-success' : 'text-foreground'}`}>
        {value}
      </span>
    </div>
  )
}

function InfoCard({ label, value, highlight }: { label: string; value: number; highlight?: boolean }) {
  return (
    <Card>
      <CardContent className="p-4">
        <p className="text-xs font-medium text-muted-foreground uppercase tracking-wide mb-1">{label}</p>
        <p className={`text-2xl font-bold tabular-nums ${highlight ? 'text-success' : 'text-foreground'}`}>{value}</p>
      </CardContent>
    </Card>
  )
}

export default function Reports() {
  const { data: reports, loading, error, isMock, refetch } = useReports()
  const report = reports[0] ?? null

  if (loading) return <LoadingState message="Loading report..." />
  if (error) return <ErrorState message={error} onRetry={refetch} />

  if (!report) {
    return (
      <EmptyState
        icon={FileText}
        title="No reports available"
        description="Complete a workflow run to generate a full analysis report with productivity metrics, test results, and remediation summary."
      />
    )
  }

  const { sections: s } = report

  const severityData = [
    { name: 'Critical', value: s.analysis.severityBreakdown.critical },
    { name: 'High',     value: s.analysis.severityBreakdown.high },
    { name: 'Medium',   value: s.analysis.severityBreakdown.medium },
    { name: 'Low',      value: s.analysis.severityBreakdown.low },
  ]

  const testData = [
    { label: 'Before',    count: s.testing.beforeCount },
    { label: 'Generated', count: s.testing.generatedCount },
    { label: 'After',     count: s.testing.afterCount },
  ]

  const productivityData = [
    { label: 'Manual',      mins: s.productivity.manualDurationMinutes },
    { label: 'AI Workflow', mins: s.productivity.aiDurationMinutes },
  ]

  return (
    <div className="space-y-6">
      <MockDataNotice isMock={isMock} />

      {/* Report header */}
      <div className="flex items-start justify-between gap-4">
        <div>
          <p className="text-lg font-semibold text-foreground">{report.repositoryName}</p>
          <p className="text-sm text-muted-foreground mt-0.5">
            Generated {new Date(report.generatedAt).toLocaleString('en-US', { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' })}
          </p>
          <div className="flex flex-wrap gap-1.5 mt-2">
            {s.repository.technologies.map((t) => (
              <span key={t} className="text-xs bg-muted text-muted-foreground px-2 py-0.5 rounded-full">{t}</span>
            ))}
          </div>
        </div>
        <Button
          variant="outline"
          size="sm"
          disabled={!report.downloadUrl}
          onClick={() => { if (report.downloadUrl) window.open(report.downloadUrl, '_blank') }}
          className="gap-1.5"
        >
          <Download className="w-3.5 h-3.5" />
          Export
        </Button>
      </div>

      {/* Stats row */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
        <InfoCard label="Files Analyzed"  value={s.repository.filesAnalyzed} />
        <InfoCard label="Total Issues"    value={s.analysis.totalIssues} />
        <InfoCard label="Issues Fixed"    value={s.remediation.issuesFixed} highlight />
        <InfoCard label="Files Modified"  value={s.remediation.filesModified} />
      </div>

      {/* Analysis + Testing row */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <Card>
          <CardHeader className="pb-3"><CardTitle>Issue Severity Breakdown</CardTitle></CardHeader>
          <CardContent>
            <div className="h-48">
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie data={severityData} cx="50%" cy="50%" innerRadius={55} outerRadius={85} paddingAngle={3} dataKey="value">
                    {severityData.map((entry) => (
                      <Cell key={entry.name} fill={SEVERITY_COLORS[entry.name] ?? '#888'} />
                    ))}
                  </Pie>
                  <Tooltip contentStyle={{ backgroundColor: 'var(--color-card)', border: '1px solid var(--color-border)', borderRadius: '6px', fontSize: '12px' }} />
                </PieChart>
              </ResponsiveContainer>
            </div>
            <div className="flex flex-wrap justify-center gap-3 mt-2">
              {severityData.map((d) => (
                <div key={d.name} className="flex items-center gap-1.5 text-xs text-muted-foreground">
                  <span className="w-2 h-2 rounded-full" style={{ backgroundColor: SEVERITY_COLORS[d.name] }} />
                  {d.name}: {d.value}
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-3"><CardTitle>Test Coverage</CardTitle></CardHeader>
          <CardContent>
            <div className="h-48">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={testData} barSize={36}>
                  <CartesianGrid strokeDasharray="3 3" stroke="var(--color-border)" />
                  <XAxis dataKey="label" tick={{ fontSize: 11, fill: 'var(--color-muted-foreground)' }} axisLine={false} tickLine={false} />
                  <YAxis tick={{ fontSize: 11, fill: 'var(--color-muted-foreground)' }} axisLine={false} tickLine={false} />
                  <Tooltip contentStyle={{ backgroundColor: 'var(--color-card)', border: '1px solid var(--color-border)', borderRadius: '6px', fontSize: '12px' }} cursor={{ fill: 'var(--color-accent)' }} />
                  <Bar dataKey="count" fill="var(--color-primary)" radius={[3, 3, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
            <div className="mt-3 pt-3 border-t border-border">
              <SectionTitle>Test Results</SectionTitle>
              <MetricRow label="Before"    value={s.testing.beforeCount} />
              <MetricRow label="Generated" value={`+${s.testing.generatedCount}`} highlight />
              <MetricRow label="Passed"    value={`${s.testing.passed} / ${s.testing.afterCount}`} highlight />
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Productivity + Remediation */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <Card>
          <CardHeader className="pb-3"><CardTitle>Productivity Impact</CardTitle></CardHeader>
          <CardContent>
            <div className="h-40">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={productivityData} layout="vertical" barSize={24}>
                  <CartesianGrid strokeDasharray="3 3" stroke="var(--color-border)" horizontal={false} />
                  <XAxis type="number" tick={{ fontSize: 11, fill: 'var(--color-muted-foreground)' }} axisLine={false} tickLine={false} unit=" min" />
                  <YAxis type="category" dataKey="label" tick={{ fontSize: 11, fill: 'var(--color-muted-foreground)' }} axisLine={false} tickLine={false} width={75} />
                  <Tooltip
                    contentStyle={{ backgroundColor: 'var(--color-card)', border: '1px solid var(--color-border)', borderRadius: '6px', fontSize: '12px' }}
                    cursor={{ fill: 'var(--color-accent)' }}
                    formatter={(v) => [`${v as number} min`]}
                  />
                  <Bar dataKey="mins" radius={[0, 3, 3, 0]}>
                    {productivityData.map((entry) => (
                      <Cell key={entry.label} fill={entry.label === 'AI Workflow' ? 'var(--color-success)' : 'var(--color-muted-foreground)'} />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </div>
            <div className="mt-3 pt-3 border-t border-border grid grid-cols-2 gap-2">
              <div>
                <p className="text-xs text-muted-foreground">Time Saved</p>
                <p className="text-xl font-bold text-success tabular-nums">{s.productivity.timeSavedMinutes} min</p>
              </div>
              <div>
                <p className="text-xs text-muted-foreground">Time Reduction</p>
                <p className="text-xl font-bold text-success tabular-nums">{s.productivity.reductionPercent}%</p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-3"><CardTitle>Remediation Summary</CardTitle></CardHeader>
          <CardContent>
            <SectionTitle>Analysis</SectionTitle>
            <MetricRow label="Files analyzed" value={s.repository.filesAnalyzed} />
            <MetricRow label="Issues detected" value={s.analysis.totalIssues} />
            <MetricRow label="Critical" value={s.analysis.severityBreakdown.critical} />
            <MetricRow label="High"     value={s.analysis.severityBreakdown.high} />
            <div className="mt-4">
              <SectionTitle>Fixes</SectionTitle>
              <MetricRow label="Issues fixed"          value={s.remediation.issuesFixed} highlight />
              <MetricRow label="Files modified"        value={s.remediation.filesModified} />
              <MetricRow label="Developer approvals"   value={s.remediation.developerApprovals} />
            </div>
            <div className="mt-4">
              <SectionTitle>Workflow</SectionTitle>
              <MetricRow label="Manual steps"              value={s.productivity.manualSteps} />
              <MetricRow label="Automated steps"           value={s.productivity.automatedSteps} highlight />
              <MetricRow label="Developer interventions"   value={s.productivity.developerInterventions} />
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
