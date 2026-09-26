import type { Repository } from '@/types/repository'
import { WorkflowStatusBadge } from '@/components/ui/status-badge'
import { Button } from '@/components/ui/button'
import { GitBranch, Play, Clock, ExternalLink, Loader2 } from 'lucide-react'
import { Card, CardContent } from '@/components/ui/card'
import { cn } from '@/lib/utils'

function formatRelativeTime(iso: string): string {
  const diff = Date.now() - new Date(iso).getTime()
  const mins = Math.floor(diff / 60000)
  if (mins < 60) return `${mins}m ago`
  const hrs = Math.floor(mins / 60)
  if (hrs < 24) return `${hrs}h ago`
  return `${Math.floor(hrs / 24)}d ago`
}

interface RepositoryCardProps {
  repository: Repository
  onStartWorkflow?: (repo: Repository) => void
  /** True while the workflow-start API request is in-flight for this card */
  isStartingWorkflow?: boolean
}

export function RepositoryCard({ repository, onStartWorkflow, isStartingWorkflow }: RepositoryCardProps) {
  const isAnalyzing = repository.status === 'analyzing'
  const isDisabled = isAnalyzing || isStartingWorkflow

  return (
    <Card className="hover:border-border/80 transition-colors">
      <CardContent className="p-5">
        <div className="flex items-start justify-between gap-3">
          {/* Left */}
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2 mb-1">
              <GitBranch className="w-4 h-4 text-muted-foreground shrink-0" />
              <p className="text-sm font-semibold text-foreground truncate">{repository.name}</p>
              {repository.language && (
                <span className="text-xs text-muted-foreground bg-muted px-1.5 py-0.5 rounded shrink-0">{repository.language}</span>
              )}
            </div>
            {repository.description && (
              <p className="text-xs text-muted-foreground truncate mb-2">{repository.description}</p>
            )}
            <div className="flex items-center gap-3 flex-wrap">
              <span className="text-xs text-muted-foreground font-mono">
                {repository.defaultBranch ?? 'main'}
              </span>
              {repository.workflowCount !== undefined && (
                <span className="text-xs text-muted-foreground">{repository.workflowCount} workflow{repository.workflowCount !== 1 ? 's' : ''}</span>
              )}
              {repository.lastAnalyzedAt && (
                <span className={cn('text-xs text-muted-foreground flex items-center gap-1')}>
                  <Clock className="w-3 h-3" />
                  {formatRelativeTime(repository.lastAnalyzedAt)}
                </span>
              )}
            </div>
          </div>
          {/* Right */}
          <div className="flex flex-col items-end gap-2 shrink-0">
            {repository.status === 'analyzed' && (
              <WorkflowStatusBadge status="completed" />
            )}
            {repository.status === 'analyzing' && (
              <WorkflowStatusBadge status="running" />
            )}
            {repository.status === 'error' && (
              <WorkflowStatusBadge status="failed" />
            )}
            <Button
              size="sm"
              variant="outline"
              disabled={isDisabled}
              onClick={() => onStartWorkflow?.(repository)}
            >
              {isStartingWorkflow
                ? <><Loader2 className="w-3.5 h-3.5 animate-spin" /> Starting…</>
                : <><Play className="w-3.5 h-3.5" /> Run Workflow</>
              }
            </Button>
          </div>
        </div>
        {repository.url && (
          <div className="mt-3 pt-3 border-t border-border flex items-center gap-1">
            <a
              href={repository.url}
              target="_blank"
              rel="noreferrer"
              className="text-xs text-muted-foreground hover:text-foreground flex items-center gap-1 transition-colors"
            >
              <ExternalLink className="w-3 h-3" />
              {repository.url.replace('https://', '')}
            </a>
          </div>
        )}
      </CardContent>
    </Card>
  )
}
