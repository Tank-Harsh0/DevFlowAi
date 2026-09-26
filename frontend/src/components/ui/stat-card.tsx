import type { LucideIcon } from 'lucide-react'
import { cn } from '@/lib/utils'
import { Card, CardContent } from '@/components/ui/card'

interface StatCardProps {
  label: string
  value: string | number
  icon?: LucideIcon
  description?: string
  trend?: 'up' | 'down' | 'neutral'
  trendLabel?: string
  className?: string
}

export function StatCard({ label, value, icon: Icon, description, className }: StatCardProps) {
  return (
    <Card className={cn('', className)}>
      <CardContent className="p-5">
        <div className="flex items-start justify-between gap-3">
          <div className="min-w-0 flex-1">
            <p className="text-xs font-medium text-muted-foreground uppercase tracking-wide mb-1">{label}</p>
            <p className="text-2xl font-bold text-foreground tabular-nums">{value}</p>
            {description && (
              <p className="text-xs text-muted-foreground mt-1">{description}</p>
            )}
          </div>
          {Icon && (
            <div className="flex items-center justify-center w-9 h-9 rounded-md bg-primary/10 shrink-0">
              <Icon className="w-4.5 h-4.5 text-primary" />
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  )
}
