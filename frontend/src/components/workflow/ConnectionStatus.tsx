import { cn } from '@/lib/utils'

type WsStatus = 'connecting' | 'connected' | 'disconnected' | 'error'

const config: Record<WsStatus, { label: string; dot: string; text: string }> = {
  connecting:   { label: 'Connecting',   dot: 'bg-amber-500 animate-pulse', text: 'text-amber-500' },
  connected:    { label: 'Live',         dot: 'bg-success animate-pulse',   text: 'text-success' },
  disconnected: { label: 'Disconnected', dot: 'bg-muted-foreground',        text: 'text-muted-foreground' },
  error:        { label: 'Error',        dot: 'bg-error',                   text: 'text-error' },
}

interface ConnectionStatusProps {
  status: WsStatus
  className?: string
}

export function ConnectionStatus({ status, className }: ConnectionStatusProps) {
  const { label, dot, text } = config[status]
  return (
    <span
      className={cn('inline-flex items-center gap-1.5 text-[10px] font-medium', text, className)}
      aria-label={`WebSocket status: ${label}`}
    >
      <span className={cn('w-1.5 h-1.5 rounded-full shrink-0', dot)} />
      {label}
    </span>
  )
}
