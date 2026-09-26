/**
 * CodeViewer — displays a code snippet with line numbers and optional
 * line highlighting.
 *
 * Does NOT fetch source files. Only displays data provided by the backend.
 * No external syntax highlighting dependency — uses a plain monospace
 * presentation which is readable and accessible.
 */

import { cn } from '@/lib/utils'

interface CodeViewerProps {
  content: string
  startLine?: number
  /** Lines to highlight (1-based, absolute) */
  highlightLines?: number[]
  language?: string
  className?: string
}

export function CodeViewer({
  content,
  startLine = 1,
  highlightLines,
  className,
}: CodeViewerProps) {
  const lines = content.split('\n')
  const highlightSet = new Set(highlightLines ?? [])

  return (
    <div className={cn('rounded-md border border-border overflow-hidden', className)}>
      {/* Code body */}
      <div className="overflow-x-auto scrollbar-thin">
        <table className="w-full text-xs font-mono leading-relaxed border-collapse">
          <tbody>
            {lines.map((line, i) => {
              const lineNum = startLine + i
              const isHighlighted = highlightSet.has(lineNum)
              return (
                <tr
                  key={lineNum}
                  className={cn(
                    'group',
                    isHighlighted ? 'bg-warning/10' : 'bg-card'
                  )}
                >
                  {/* Line number gutter */}
                  <td
                    className="select-none text-right pr-3 pl-3 text-muted-foreground/50 border-r border-border w-10 shrink-0"
                    aria-hidden="true"
                  >
                    {lineNum}
                  </td>
                  {/* Code content */}
                  <td className="pl-3 pr-4 py-0.5 whitespace-pre text-foreground">
                    {isHighlighted && (
                      <span
                        className="inline-block w-1 h-full bg-warning rounded-sm mr-1.5 -ml-1.5 shrink-0"
                        aria-hidden="true"
                      />
                    )}
                    {line || ' '}
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
