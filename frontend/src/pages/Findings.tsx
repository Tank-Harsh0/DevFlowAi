import { useState, useMemo, useCallback } from 'react'
import { Search, AlertTriangle, SlidersHorizontal } from 'lucide-react'
import { Input } from '@/components/ui/input'
import { Button } from '@/components/ui/button'
import { Card } from '@/components/ui/card'
import { FindingRow } from '@/components/findings/FindingRow'
import { FindingDetail } from '@/components/findings/FindingDetail'
import { EmptyState, LoadingState, ErrorState } from '@/components/ui/states'
import { MockDataNotice } from '@/components/ui/mock-notice'
import { SeverityBadge, FindingStatusBadge } from '@/components/ui/status-badge'
import { useFindings } from '@/hooks/useFindings'
import { workflowsService } from '@/services/workflows'
import type { Finding, FindingSeverity, FindingStatus } from '@/types/finding'

const SEVERITIES: FindingSeverity[] = ['critical', 'high', 'medium', 'low']
const STATUSES: FindingStatus[] = ['open', 'fixed', 'dismissed', 'pending_fix']
const AGENTS = [
  { value: 'code_review',   label: 'Code Review' },
  { value: 'security',      label: 'Security' },
  { value: 'test_analysis', label: 'Test Analysis' },
  { value: 'documentation', label: 'Documentation' },
]

function FilterChip({ label, active, onClick }: { label: React.ReactNode; active: boolean; onClick: () => void }) {
  return (
    <button
      type="button"
      onClick={onClick}
      className={`px-2.5 py-1 text-xs rounded-full border transition-colors ${
        active
          ? 'border-primary/40 bg-primary/10 text-primary'
          : 'border-border text-muted-foreground hover:text-foreground hover:border-border/80'
      }`}
    >
      {label}
    </button>
  )
}

export default function Findings() {
  const [search, setSearch] = useState('')
  const [selectedSeverities, setSelectedSeverities] = useState<Set<FindingSeverity>>(new Set())
  const [selectedStatuses, setSelectedStatuses] = useState<Set<FindingStatus>>(new Set())
  const [selectedAgent, setSelectedAgent] = useState<string | null>(null)
  const [selectedFinding, setSelectedFinding] = useState<Finding | null>(null)
  const [showFilters, setShowFilters] = useState(false)
  const [approving, setApproving] = useState(false)

  // Fetch all findings — server-side filtering will be used in the future
  // when the backend supports query params for severity/status/agent
  const { data: allFindings, loading, error, isMock, refetch } = useFindings()

  const filtered = useMemo(() => {
    return allFindings.filter((f) => {
      if (search && !f.title.toLowerCase().includes(search.toLowerCase()) && !f.location.file.toLowerCase().includes(search.toLowerCase())) return false
      if (selectedSeverities.size > 0 && !selectedSeverities.has(f.severity)) return false
      if (selectedStatuses.size > 0 && !selectedStatuses.has(f.status)) return false
      if (selectedAgent && f.agent !== selectedAgent) return false
      return true
    })
  }, [allFindings, search, selectedSeverities, selectedStatuses, selectedAgent])

  function toggleSeverity(s: FindingSeverity) {
    setSelectedSeverities((prev) => {
      const next = new Set(prev)
      if (next.has(s)) { next.delete(s) } else { next.add(s) }
      return next
    })
  }

  function toggleStatus(s: FindingStatus) {
    setSelectedStatuses((prev) => {
      const next = new Set(prev)
      if (next.has(s)) { next.delete(s) } else { next.add(s) }
      return next
    })
  }

  const severityCounts = useMemo(() => {
    const counts: Record<string, number> = {}
    allFindings.forEach((f) => { counts[f.severity] = (counts[f.severity] ?? 0) + 1 })
    return counts
  }, [allFindings])

  const handleApprove = useCallback(async () => {
    if (!selectedFinding?.fixProposal) return
    setApproving(true)
    try {
      await workflowsService.submitApproval(
        selectedFinding.workflowId,
        selectedFinding.fixProposal.id,
        true
      )
      refetch()
      setSelectedFinding(null)
    } catch (err) {
      alert(err instanceof Error ? err.message : 'Approval failed')
    } finally {
      setApproving(false)
    }
  }, [selectedFinding, refetch])

  const handleReject = useCallback(async () => {
    if (!selectedFinding?.fixProposal) return
    setApproving(true)
    try {
      await workflowsService.submitApproval(
        selectedFinding.workflowId,
        selectedFinding.fixProposal.id,
        false
      )
      refetch()
      setSelectedFinding(null)
    } catch (err) {
      alert(err instanceof Error ? err.message : 'Rejection failed')
    } finally {
      setApproving(false)
    }
  }, [selectedFinding, refetch])

  return (
    <div className="space-y-4">
      <div className="flex items-center gap-3 flex-wrap">
        <MockDataNotice isMock={isMock} />
      </div>

      {/* Header + search + filters */}
      <div className="flex items-center gap-3 flex-wrap">
        <div className="relative flex-1 min-w-48 max-w-sm">
          <Search className="absolute left-2.5 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-muted-foreground" />
          <Input
            placeholder="Search findings..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="pl-8 h-8 text-sm"
          />
        </div>
        <Button
          variant={showFilters ? 'secondary' : 'outline'}
          size="sm"
          onClick={() => setShowFilters(!showFilters)}
          className="gap-1.5"
        >
          <SlidersHorizontal className="w-3.5 h-3.5" />
          Filters
          {(selectedSeverities.size + selectedStatuses.size + (selectedAgent ? 1 : 0)) > 0 && (
            <span className="bg-primary text-primary-foreground rounded-full w-4 h-4 text-[10px] flex items-center justify-center">
              {selectedSeverities.size + selectedStatuses.size + (selectedAgent ? 1 : 0)}
            </span>
          )}
        </Button>
        <span className="text-xs text-muted-foreground ml-auto">
          {filtered.length} of {allFindings.length} findings
        </span>
      </div>

      {/* Filter panel */}
      {showFilters && (
        <div className="flex flex-wrap gap-4 p-3 rounded-md bg-card border border-border">
          <div>
            <p className="text-xs font-medium text-muted-foreground mb-1.5">Severity</p>
            <div className="flex gap-1.5 flex-wrap">
              {SEVERITIES.map((s) => (
                <FilterChip key={s} label={<SeverityBadge severity={s} />} active={selectedSeverities.has(s)} onClick={() => toggleSeverity(s)} />
              ))}
            </div>
          </div>
          <div>
            <p className="text-xs font-medium text-muted-foreground mb-1.5">Status</p>
            <div className="flex gap-1.5 flex-wrap">
              {STATUSES.map((s) => (
                <FilterChip key={s} label={<FindingStatusBadge status={s} />} active={selectedStatuses.has(s)} onClick={() => toggleStatus(s)} />
              ))}
            </div>
          </div>
          <div>
            <p className="text-xs font-medium text-muted-foreground mb-1.5">Agent</p>
            <div className="flex gap-1.5 flex-wrap">
              {AGENTS.map((a) => (
                <FilterChip
                  key={a.value}
                  label={a.label}
                  active={selectedAgent === a.value}
                  onClick={() => setSelectedAgent(selectedAgent === a.value ? null : a.value)}
                />
              ))}
            </div>
          </div>
        </div>
      )}

      {/* Severity summary */}
      {!loading && !error && (
        <div className="flex gap-3 flex-wrap">
          {SEVERITIES.map((s) => (
            <div key={s} className="flex items-center gap-1.5 text-xs text-muted-foreground">
              <SeverityBadge severity={s} />
              <span className="tabular-nums">{severityCounts[s] ?? 0}</span>
            </div>
          ))}
        </div>
      )}

      {loading && <LoadingState message="Loading findings..." />}
      {!loading && error && <ErrorState message={error} onRetry={refetch} />}

      {!loading && !error && (
        <div className="grid grid-cols-1 lg:grid-cols-5 gap-4">
          {/* Finding list */}
          <Card className="lg:col-span-2 overflow-hidden">
            {filtered.length === 0 ? (
              <EmptyState
                icon={AlertTriangle}
                title={allFindings.length === 0 ? 'No findings' : 'No findings match filters'}
                description={
                  allFindings.length === 0
                    ? 'Run a workflow to detect issues.'
                    : 'Try adjusting your search or filter criteria.'
                }
              />
            ) : (
              <div className="divide-y divide-border">
                {filtered.map((f) => (
                  <FindingRow
                    key={f.id}
                    finding={f}
                    selected={selectedFinding?.id === f.id}
                    onClick={() => setSelectedFinding(f)}
                  />
                ))}
              </div>
            )}
          </Card>

          {/* Finding detail */}
          <Card className="lg:col-span-3 overflow-hidden">
            {selectedFinding ? (
              <FindingDetail
                finding={selectedFinding}
                onClose={() => setSelectedFinding(null)}
                onApprove={approving ? undefined : () => void handleApprove()}
                onReject={approving ? undefined : () => void handleReject()}
              />
            ) : (
              <EmptyState
                icon={AlertTriangle}
                title="Select a finding"
                description="Click a finding on the left to view its details, evidence, and suggested fix."
              />
            )}
          </Card>
        </div>
      )}
    </div>
  )
}
