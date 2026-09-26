/**
 * FindingDetailPage — full-page view for a single finding, accessible via
 * /findings/:id. Enables deep-linking to a specific finding.
 *
 * Uses useFinding() to load the finding by ID from the backend (or mock
 * fallback when the backend is unreachable). Does NOT fabricate finding data.
 */

import { useParams, useNavigate, Link } from 'react-router-dom'
import { ArrowLeft } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { LoadingState, ErrorState } from '@/components/ui/states'
import { MockDataNotice } from '@/components/ui/mock-notice'
import { FindingDetail } from '@/components/findings/FindingDetail'
import { useFinding } from '@/hooks/useFinding'

export default function FindingDetailPage() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()

  const { data: finding, loading, error, isMock, refetch } = useFinding(id ?? null)

  if (loading) {
    return <LoadingState message="Loading finding…" />
  }

  if (error) {
    return <ErrorState message={error} onRetry={refetch} />
  }

  if (!finding) {
    return (
      <div className="flex flex-col items-center justify-center gap-4 py-24 text-center">
        <p className="text-sm font-medium text-foreground">Finding not found</p>
        <p className="text-xs text-muted-foreground">
          The finding with ID <code className="font-mono">{id}</code> does not exist or is no longer
          available.
        </p>
        <Button variant="outline" size="sm" asChild>
          <Link to="/findings">Back to Findings</Link>
        </Button>
      </div>
    )
  }

  return (
    <div className="flex flex-col gap-4 h-full">
      {/* Mock notice */}
      {isMock && <MockDataNotice isMock={isMock} />}

      {/* Back navigation */}
      <div className="flex items-center gap-2">
        <Button
          variant="ghost"
          size="sm"
          className="gap-1.5 text-muted-foreground"
          onClick={() => navigate(-1)}
        >
          <ArrowLeft className="w-3.5 h-3.5" />
          Back
        </Button>
        <span className="text-xs text-muted-foreground">/</span>
        <Link to="/findings" className="text-xs text-muted-foreground hover:text-foreground">
          Findings
        </Link>
        <span className="text-xs text-muted-foreground">/</span>
        <span className="text-xs text-foreground truncate max-w-xs">{finding.title}</span>
      </div>

      {/* Full-width detail panel */}
      <div className="flex-1 min-h-0 rounded-lg border border-border bg-card overflow-hidden">
        <FindingDetail
          finding={finding}
          onApproved={refetch}
          onRejected={refetch}
        />
      </div>
    </div>
  )
}
