import { cn } from '@/lib/utils'

/**
 * MockDataNotice — shown when live API data is unavailable and the UI
 * is displaying mock data. Always clearly distinguishes mock from real data.
 */
interface MockDataNoticeProps {
  isMock: boolean
  className?: string
}

export function MockDataNotice({ isMock, className }: MockDataNoticeProps) {
  if (!isMock) return null
  return (
    <div className={cn('flex items-center gap-2 text-xs text-amber-500 px-1', className)}>
      <span className="w-1.5 h-1.5 rounded-full bg-amber-500 shrink-0" />
      Backend unreachable — displaying mock data for UI development
    </div>
  )
}
