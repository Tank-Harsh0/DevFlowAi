import { useState, useMemo, useCallback, useEffect } from 'react'
import { Search, AlertTriangle, SlidersHorizontal, X, ExternalLink } from 'lucide-react'
import { useSearchParams, Link } from 'react-router-dom'
import { Input } from '@/components/ui/input'
import { Button } from '@/components/ui/button'
import { Card } from '@/components/ui/card'
import { FindingRow } from '@/components/findings/FindingRow'
import { FindingDetail } from '@/components/findings/FindingDetail'
import { EmptyState, LoadingState, ErrorState } from '@/components/ui/states'
import { MockDataNotice } from '@/components/ui/mock-notice'
import { SeverityBadge, FindingStatusBadge } from '@/components/ui/status-badge'
import { useFindings } from '@/hooks/useFindings'
import type { Finding, FindingSeverity, FindingStatus } from '@/types/finding'

// ── Constants ──────────────────────────────────────────────────────────────────

const SEVERITIES: FindingSeverity[] = ['critical', 'high', 'medium', 'low', 'info']

const STATUSES: FindingStatus[] = [
  'open', 'in_review', 'approved', 'rejected',
  'pending_fix', 'fixed', 'verified', 'verification_failed', 'dismissed',
]

const AGENTS = [
  { value: 'code_review',   label: 'Code Review' },
  { value: 'security',      label: 'Security' },
  { value: 'test_analysis', label: 'Test Analysis' },
  { value: 'documentation', label: 'Documentation' },
]

// ── Helpers ────────────────────────────────────────────────────────────────────

function countBySeverity(findings: Finding[]): Record<FindingSeverity, number> {
  const counts: Record<FindingSeverity, number> = {
    critical: 0, high: 0, medium: 0, low: 0, info: 0,
  }
  findings.forEach((f) => { counts[f.severity] = (counts[f.severity] ?? 0) + 1 })
  return counts
}

// ── FilterChip ─────────────────────────────────────────────────────────────────

function FilterChip({
  label,
  active,
  onClick,
}: {
  label: React.ReactNode
  active: boolean
  onClick: () => void
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      className={`px-2.5 py-1 text-xs rounded-full border transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring ${
        active
          ? 'border-primary/40 bg-primary/10 text-primary'
          : 'border-border text-muted-foreground hover:text-foreground hover:border-border/80'
      }`}
    >
      {label}
    </button>
  )
}

// ── Header ─────────────────────────────────────────────────────────────────────

function FindingsHeader({
  total,
  counts,
  workflowId,
}: {
  total: number
  counts: Record<FindingSeverity, number>
  workflowId: string | null
}) {
  const hasAny = total > 0
  return (
    <div className="flex items-baseline gap-6 flex-wrap">
      <div>
        <h1 className="text-base font-semibold text-foreground">
          {total} finding{total !== 1 ? 's' : ''}
        </h1>
        {workflowId && (
          <p className="text-xs text-muted-foreground mt-0.5">
            Filtered by workflow ·{' '}
            <Link
              to={`/workflow?workflowId=${workflowId}`}
              className="text-primary hover:underline inline-flex items-center gap-0.5"
            >
              View workflow <ExternalLink className="w-2.5 h-2.5" />
            </Link>
          </p>
        )}
      </div>
      {hasAny && (
        <div className="flex items-center gap-3 flex-wrap">
          {SEVERITIES.filter((s) => counts[s] > 0).map((s) => (
            <div key={s} className="flex items-center gap-1.5">
              <SeverityBadge severity={s} />
              <span className="text-xs tabular-nums text-muted-foreground">{counts[s]}</span>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

// ── Page ───────────────────────────────────────────────────────────────────────

export default function Findings() {
  const [searchParams, setSearchParams] = useSearchParams()

  // Read workflowId from URL — used when navigating from the Workflow page
  const workflowIdParam = searchParams.get('workflowId')

  const [search, setSearch]                       = useState('')
  const [selectedSeverities, setSelectedSeverities] = useState<Set<FindingSeverity>>(new Set())
  const [selectedStatuses, setSelectedStatuses]   = useState<Set<FindingStatus>>(new Set())
  const [selectedAgent, setSelectedAgent]         = useState<string | null>(null)
  // workflowId filter — initialised from URL param if present
  const [selectedWorkflowId, setSelectedWorkflowId] = useState<string | null>(workflowIdParam)
  const [selectedIdx, setSelectedIdx]             = useState<number | null>(null)
  const [showFilters, setShowFilters]             = useState(false)

  // Sync selectedWorkflowId when the URL param changes (e.g. navigating from Workflow page)
  useEffect(() => {
    setSelectedWorkflowId(workflowIdParam)
  }, [workflowIdParam])

  // Fetch all findings from the API (server-side filters can be enabled later)
  const { data: allFindings, loading, error, isMock, refetch } = useFindings()

  // ── Filtering (client-side until backend supports query params) ────────────
  const filtered = useMemo<Finding[]>(() => {
    const q = search.toLowerCase()
    return allFindings.filter((f) => {
      if (
        q &&
        !f.title.toLowerCase().includes(q) &&
        !f.location.file.toLowerCase().includes(q) &&
        !f.description.toLowerCase().includes(q)
      ) return false
      if (selectedSeverities.size > 0 && !selectedSeverities.has(f.severity)) return false
      if (selectedStatuses.size > 0 && !selectedStatuses.has(f.status)) return false
      if (selectedAgent && f.agent !== selectedAgent) return false
      if (selectedWorkflowId && f.workflowId !== selectedWorkflowId) return false
      return true
    })
  }, [allFindings, search, selectedSeverities, selectedStatuses, selectedAgent, selectedWorkflowId])

  const selectedFinding = selectedIdx !== null ? filtered[selectedIdx] ?? null : null

  const severityCounts = useMemo(() => countBySeverity(filtered), [filtered])

  const activeFilterCount =
    selectedSeverities.size + selectedStatuses.size + (selectedAgent ? 1 : 0) + (selectedWorkflowId ? 1 : 0)

  // ── Toggle helpers ─────────────────────────────────────────────────────────
  function toggleSeverity(s: FindingSeverity) {
    setSelectedSeverities((prev) => {
      const next = new Set(prev)
      if (next.has(s)) next.delete(s); else next.add(s)
      return next
    })
    setSelectedIdx(null)
  }

  function toggleStatus(s: FindingStatus) {
    setSelectedStatuses((prev) => {
      const next = new Set(prev)
      if (next.has(s)) next.delete(s); else next.add(s)
      return next
    })
    setSelectedIdx(null)
  }

  function clearFilters() {
    setSearch('')
    setSelectedSeverities(new Set())
    setSelectedStatuses(new Set())
    setSelectedAgent(null)
    setSelectedWorkflowId(null)
    setSelectedIdx(null)
    // Remove workflowId from URL
    setSearchParams({})
  }

  // ── Navigation ─────────────────────────────────────────────────────────────
  const handlePrev = useCallback(() => {
    setSelectedIdx((i) => (i !== null && i > 0 ? i - 1 : i))
  }, [])

  const handleNext = useCallback(() => {
    setSelectedIdx((i) => (i !== null && i < filtered.length - 1 ? i + 1 : i))
  }, [filtered.length])

  // ── Approval / Rejection callbacks ─────────────────────────────────────────
  const handleApproved = useCallback(() => {
    // Refetch to get the latest state from backend after approval
    refetch()
  }, [refetch])

  const handleRejected = useCallback(() => {
    refetch()
  }, [refetch])

  // ── Render ──────────────────────────────────────────────────────────────────
  return (
    <div className="flex flex-col gap-4 h-full">
      {/* Mock data notice */}
      {isMock && (
        <div className="flex items-center gap-3 flex-wrap">
          <MockDataNotice isMock={isMock} />
        </div>
      )}

      {/* Page header */}
      {!loading && !error && (
        <FindingsHeader
          total={filtered.length}
          counts={severityCounts}
          workflowId={selectedWorkflowId}
        />
      )}

      {/* Search + filter toolbar */}
      <div className="flex items-center gap-2 flex-wrap">
        <div className="relative flex-1 min-w-48 max-w-sm">
          <Search className="absolute left-2.5 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-muted-foreground pointer-events-none" />
          <Input
            placeholder="Search findings..."
            value={search}
            onChange={(e) => { setSearch(e.target.value); setSelectedIdx(null) }}
            className="pl-8 h-8 text-sm"
            aria-label="Search findings"
          />
          {search && (
            <button
              type="button"
              onClick={() => { setSearch(''); setSelectedIdx(null) }}
              className="absolute right-2.5 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground"
              aria-label="Clear search"
            >
              <X className="w-3.5 h-3.5" />
            </button>
          )}
        </div>

        <Button
          variant={showFilters ? 'secondary' : 'outline'}
          size="sm"
          onClick={() => setShowFilters(!showFilters)}
          className="gap-1.5"
          aria-expanded={showFilters}
          aria-controls="filter-panel"
        >
          <SlidersHorizontal className="w-3.5 h-3.5" />
          Filters
          {activeFilterCount > 0 && (
            <span className="bg-primary text-primary-foreground rounded-full w-4 h-4 text-[10px] flex items-center justify-center">
              {activeFilterCount}
            </span>
          )}
        </Button>

        {(activeFilterCount > 0 || search) && (
          <Button variant="ghost" size="sm" onClick={clearFilters} className="text-muted-foreground gap-1.5">
            <X className="w-3.5 h-3.5" />
            Clear filters
          </Button>
        )}

        <span className="text-xs text-muted-foreground ml-auto tabular-nums">
          {filtered.length} of {allFindings.length}
        </span>
      </div>

      {/* Filter panel */}
      {showFilters && (
        <div id="filter-panel" className="flex flex-wrap gap-5 p-4 rounded-md bg-card border border-border">
          <div>
            <p className="text-xs font-medium text-muted-foreground mb-2">Severity</p>
            <div className="flex gap-1.5 flex-wrap">
              {SEVERITIES.map((s) => (
                <FilterChip
                  key={s}
                  label={<SeverityBadge severity={s} />}
                  active={selectedSeverities.has(s)}
                  onClick={() => toggleSeverity(s)}
                />
              ))}
            </div>
          </div>
          <div>
            <p className="text-xs font-medium text-muted-foreground mb-2">Status</p>
            <div className="flex gap-1.5 flex-wrap">
              {STATUSES.map((s) => (
                <FilterChip
                  key={s}
                  label={<FindingStatusBadge status={s} />}
                  active={selectedStatuses.has(s)}
                  onClick={() => toggleStatus(s)}
                />
              ))}
            </div>
          </div>
          <div>
            <p className="text-xs font-medium text-muted-foreground mb-2">Agent</p>
            <div className="flex gap-1.5 flex-wrap">
              {AGENTS.map((a) => (
                <FilterChip
                  key={a.value}
                  label={a.label}
                  active={selectedAgent === a.value}
                  onClick={() => {
                    setSelectedAgent(selectedAgent === a.value ? null : a.value)
                    setSelectedIdx(null)
                  }}
                />
              ))}
            </div>
          </div>
          {/* Workflow filter chip — shows only when a workflowId is active */}
          {selectedWorkflowId && (
            <div>
              <p className="text-xs font-medium text-muted-foreground mb-2">Workflow</p>
              <FilterChip
                label={`Workflow: ${selectedWorkflowId}`}
                active={true}
                onClick={() => {
                  setSelectedWorkflowId(null)
                  setSearchParams({})
                  setSelectedIdx(null)
                }}
              />
            </div>
          )}
        </div>
      )}

      {/* States */}
      {loading && <LoadingState message="Loading findings..." />}
      {!loading && error && <ErrorState message={error} onRetry={refetch} />}

      {/* Main findings layout */}
      {!loading && !error && (
        <div className="grid grid-cols-1 lg:grid-cols-5 gap-4 flex-1 min-h-0">

          {/* Finding list */}
          <Card className="lg:col-span-2 overflow-hidden flex flex-col">
            {filtered.length === 0 ? (
              <EmptyState
                icon={AlertTriangle}
                title={allFindings.length === 0 ? 'No findings' : 'No findings match filters'}
                description={
                  allFindings.length === 0
                    ? 'Run a workflow to detect issues.'
                    : 'Try adjusting your search or filters.'
                }
              />
            ) : (
              <div
                className="divide-y divide-border overflow-y-auto scrollbar-thin flex-1"
                role="list"
                aria-label="Findings list"
              >
                {filtered.map((f, idx) => (
                  <div key={f.id} role="listitem">
                    <FindingRow
                      finding={f}
                      selected={selectedIdx === idx}
                      onClick={() => setSelectedIdx(idx)}
                    />
                  </div>
                ))}
              </div>
            )}
          </Card>

          {/* Finding detail */}
          <Card className="lg:col-span-3 overflow-hidden flex flex-col min-h-0">
            {selectedFinding ? (
              <FindingDetail
                finding={selectedFinding}
                index={selectedIdx ?? 0}
                total={filtered.length}
                onClose={() => setSelectedIdx(null)}
                onPrev={handlePrev}
                onNext={handleNext}
                onApproved={handleApproved}
                onRejected={handleRejected}
              />
            ) : (
              <EmptyState
                icon={AlertTriangle}
                title="Select a finding"
                description="Click a finding on the left to view its details, evidence, and proposed fix."
              />
            )}
          </Card>
        </div>
      )}
    </div>
  )
}
