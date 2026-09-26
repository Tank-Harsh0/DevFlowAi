import { useState, useCallback } from 'react'
import { Plus, Search, GitBranch } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { RepositoryCard } from '@/components/repositories/RepositoryCard'
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card'
import { Separator } from '@/components/ui/separator'
import { EmptyState, LoadingState, ErrorState } from '@/components/ui/states'
import { MockDataNotice } from '@/components/ui/mock-notice'
import { useRepositories } from '@/hooks/useRepositories'
import { repositoriesService } from '@/services/repositories'
import type { Repository, AddRepositoryRequest } from '@/types/repository'

function AddRepositoryModal({ onClose, onAdded }: { onClose: () => void; onAdded: () => void }) {
  const [url, setUrl] = useState('')
  const [branch, setBranch] = useState('main')
  const [submitting, setSubmitting] = useState(false)
  const [submitError, setSubmitError] = useState<string | null>(null)

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    if (!url.trim()) return
    setSubmitting(true)
    setSubmitError(null)
    try {
      const payload: AddRepositoryRequest = { url: url.trim(), defaultBranch: branch.trim() || 'main' }
      await repositoriesService.add(payload)
      onAdded()
      onClose()
    } catch (err) {
      setSubmitError(err instanceof Error ? err.message : 'Failed to add repository')
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-background/80 backdrop-blur-sm">
      <Card className="w-full max-w-md mx-4">
        <CardHeader>
          <CardTitle>Add Repository</CardTitle>
          <CardDescription>
            Connect a Git repository to start AI-powered workflow analysis.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={(e) => void handleSubmit(e)} className="space-y-4">
            <div className="space-y-1.5">
              <label className="text-xs font-medium text-foreground" htmlFor="repo-url">
                Repository URL
              </label>
              <Input
                id="repo-url"
                placeholder="https://github.com/owner/repo"
                value={url}
                onChange={(e) => setUrl(e.target.value)}
                required
              />
            </div>
            <div className="space-y-1.5">
              <label className="text-xs font-medium text-foreground" htmlFor="repo-branch">
                Default Branch
              </label>
              <Input
                id="repo-branch"
                placeholder="main"
                value={branch}
                onChange={(e) => setBranch(e.target.value)}
              />
            </div>
            {submitError && (
              <div className="p-3 rounded-md bg-error/10 border border-error/20">
                <p className="text-xs text-error">{submitError}</p>
              </div>
            )}
            <Separator />
            <div className="flex gap-2 justify-end">
              <Button type="button" variant="outline" size="sm" onClick={onClose} disabled={submitting}>
                Cancel
              </Button>
              <Button type="submit" size="sm" disabled={submitting || !url.trim()}>
                {submitting ? 'Adding...' : 'Add Repository'}
              </Button>
            </div>
          </form>
        </CardContent>
      </Card>
    </div>
  )
}

export default function Repositories() {
  const [search, setSearch] = useState('')
  const [showAddModal, setShowAddModal] = useState(false)

  const { data: repositories, loading, error, isMock, refetch } = useRepositories()

  const handleStartWorkflow = useCallback((_repo: Repository) => {
    // Phase 4: connect to workflowsService.start(_repo.id) and navigate to /workflow
    void _repo
    alert('Backend integration pending — workflow start will be enabled in Phase 4.')
  }, [])

  const filtered = repositories.filter(
    (r) =>
      r.name.toLowerCase().includes(search.toLowerCase()) ||
      r.description?.toLowerCase().includes(search.toLowerCase())
  )

  return (
    <>
      {showAddModal && (
        <AddRepositoryModal
          onClose={() => setShowAddModal(false)}
          onAdded={refetch}
        />
      )}

      <div className="space-y-5">
        {/* Header row */}
        <div className="flex items-center justify-between gap-4 flex-wrap">
          <div className="flex items-center gap-3 flex-1 min-w-0">
            <div className="relative max-w-xs flex-1">
              <Search className="absolute left-2.5 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-muted-foreground" />
              <Input
                placeholder="Search repositories..."
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                className="pl-8 h-8 text-sm"
              />
            </div>
            <MockDataNotice isMock={isMock} />
          </div>
          <Button size="sm" onClick={() => setShowAddModal(true)}>
            <Plus className="w-4 h-4" />
            Add Repository
          </Button>
        </div>

        {/* States */}
        {loading && <LoadingState message="Loading repositories..." />}

        {!loading && error && (
          <ErrorState message={error} onRetry={refetch} />
        )}

        {!loading && !error && filtered.length === 0 && (
          <EmptyState
            icon={GitBranch}
            title={search ? `No repositories matching "${search}"` : 'No repositories connected'}
            description={
              search
                ? 'Try a different search term.'
                : 'Add your first repository to start AI-powered workflow analysis.'
            }
            action={
              !search ? (
                <Button size="sm" onClick={() => setShowAddModal(true)}>
                  <Plus className="w-4 h-4" />
                  Add Repository
                </Button>
              ) : undefined
            }
          />
        )}

        {!loading && !error && filtered.length > 0 && (
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            {filtered.map((repo) => (
              <RepositoryCard
                key={repo.id}
                repository={repo}
                onStartWorkflow={handleStartWorkflow}
              />
            ))}
          </div>
        )}
      </div>
    </>
  )
}
