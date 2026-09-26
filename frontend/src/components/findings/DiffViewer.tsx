/**
 * DiffViewer — renders a before/after code diff.
 *
 * Supports two input modes:
 *  1. Unified patch string — if diff.before starts with "---" or lines include
 *     "+"/"-" prefixed lines, it is parsed as a unified diff.
 *  2. Before/after strings — simple line-by-line comparison with removed then
 *     added blocks (fallback for when only before/after text is available).
 *
 * Does NOT generate diffs — only renders data provided by the backend.
 * Never fabricates a diff when the backend does not supply one.
 */

import { cn } from '@/lib/utils'
import type { CodeDiff } from '@/types/finding'

interface DiffLine {
  type: 'removed' | 'added' | 'context'
  content: string
}

/**
 * Try to parse the before string as a unified diff patch.
 * Returns parsed lines if the string looks like a unified diff,
 * otherwise returns null so the before/after fallback is used.
 */
function tryParseUnifiedDiff(patch: string): DiffLine[] | null {
  const lines = patch.split('\n')
  // A unified diff starts with --- or has lines starting with +/-/ prefix
  const hasUnifiedMarkers = lines.some(
    (l) => l.startsWith('---') || l.startsWith('+++') || l.startsWith('@@ ')
  )
  const hasPlusMinus = lines.some((l) => l.startsWith('+') || l.startsWith('-'))

  if (!hasUnifiedMarkers && !hasPlusMinus) return null

  const result: DiffLine[] = []
  for (const line of lines) {
    if (line.startsWith('---') || line.startsWith('+++') || line.startsWith('@@ ')) {
      // skip file headers and hunk headers
      continue
    }
    if (line.startsWith('+')) {
      result.push({ type: 'added', content: line.slice(1) })
    } else if (line.startsWith('-')) {
      result.push({ type: 'removed', content: line.slice(1) })
    } else {
      // context line (leading space) or empty
      result.push({ type: 'context', content: line.startsWith(' ') ? line.slice(1) : line })
    }
  }
  return result.length > 0 ? result : null
}

/**
 * Produces a simple line-by-line diff from before/after strings.
 * For a real diff the backend should provide a unified patch string;
 * this function is a fallback for when only before/after text is available.
 */
function buildDiffLines(before: string, after: string): DiffLine[] {
  const beforeLines = before.split('\n')
  const afterLines = after.split('\n')
  const lines: DiffLine[] = []

  beforeLines.forEach((line) => {
    lines.push({ type: 'removed', content: line })
  })
  afterLines.forEach((line) => {
    lines.push({ type: 'added', content: line })
  })

  return lines
}

const lineConfig = {
  removed: {
    prefix: '−',
    row: 'bg-error/8 hover:bg-error/12',
    gutter: 'bg-error/15 text-error/70',
    text: 'text-error/90',
  },
  added: {
    prefix: '+',
    row: 'bg-success/8 hover:bg-success/12',
    gutter: 'bg-success/15 text-success/70',
    text: 'text-success/90',
  },
  context: {
    prefix: ' ',
    row: 'bg-card hover:bg-accent/30',
    gutter: 'bg-muted text-muted-foreground/50',
    text: 'text-foreground',
  },
} as const

interface DiffViewerProps {
  diff: CodeDiff
  className?: string
}

export function DiffViewer({ diff, className }: DiffViewerProps) {
  // Try to parse before as a unified patch first, fall back to before/after comparison
  const lines =
    tryParseUnifiedDiff(diff.before) ?? buildDiffLines(diff.before, diff.after)

  if (lines.length === 0) {
    return (
      <p className="text-xs text-muted-foreground py-2">
        No diff content available.
      </p>
    )
  }

  const removedCount = lines.filter((l) => l.type === 'removed').length
  const addedCount = lines.filter((l) => l.type === 'added').length

  return (
    <div
      className={cn(
        'rounded-md border border-border overflow-hidden text-xs font-mono',
        className
      )}
      role="region"
      aria-label="Code diff"
    >
      {/* File header bar */}
      <div className="flex items-center gap-2 px-3 py-1.5 bg-muted border-b border-border">
        <span className="text-[10px] font-medium text-muted-foreground uppercase tracking-wide">
          Diff
        </span>
        {diff.language && (
          <span className="text-[10px] text-muted-foreground/60">{diff.language}</span>
        )}
        <div className="ml-auto flex items-center gap-3">
          <span
            className="text-[10px] text-error font-medium"
            aria-label={`${removedCount} lines removed`}
          >
            −{removedCount}
          </span>
          <span
            className="text-[10px] text-success font-medium"
            aria-label={`${addedCount} lines added`}
          >
            +{addedCount}
          </span>
        </div>
      </div>

      {/* Diff lines */}
      <div className="overflow-x-auto scrollbar-thin">
        <table className="w-full border-collapse leading-relaxed">
          <tbody>
            {lines.map((line, idx) => {
              const cfg = lineConfig[line.type]
              return (
                <tr key={idx} className={cn('group', cfg.row)}>
                  {/* Gutter: +/- prefix */}
                  <td
                    className={cn(
                      'select-none text-center w-8 border-r border-border/50 py-0.5',
                      cfg.gutter
                    )}
                    aria-hidden="true"
                  >
                    {cfg.prefix}
                  </td>
                  {/* Line content */}
                  <td className={cn('pl-3 pr-4 py-0.5 whitespace-pre', cfg.text)}>
                    {line.content || ' '}
                  </td>
                </tr>
              )
            })}
          </tbody>
        </table>
      </div>
    </div>
  )
}
