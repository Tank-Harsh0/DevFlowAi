import { useState, useEffect, useRef } from 'react'
import { WEBSOCKET_URL } from '@/services/api'
import type { WorkflowEvent } from '@/types/workflow'

type WsStatus = 'connecting' | 'connected' | 'disconnected' | 'error'

interface UseWebSocketOptions {
  workflowId: string | null
  onEvent?: (event: WorkflowEvent) => void
  enabled?: boolean
}

export function useWebSocket({ workflowId, onEvent, enabled = true }: UseWebSocketOptions) {
  const [status, setStatus] = useState<WsStatus>('disconnected')
  const wsRef = useRef<WebSocket | null>(null)
  const reconnectTimer = useRef<ReturnType<typeof setTimeout> | null>(null)
  const onEventRef = useRef<typeof onEvent>(undefined)

  // Sync callback ref inside an effect to satisfy react-hooks/refs
  useEffect(() => {
    onEventRef.current = onEvent
  }, [onEvent])

  useEffect(() => {
    if (!workflowId || !enabled) return

    let cancelled = false

    function connect() {
      if (cancelled) return
      setStatus('connecting')
      const ws = new WebSocket(`${WEBSOCKET_URL}/api/v1/ws/workflows/${workflowId}`)
      wsRef.current = ws

      ws.onopen = () => {
        if (!cancelled) setStatus('connected')
      }

      ws.onmessage = (e: MessageEvent) => {
        try {
          const event = JSON.parse(e.data as string) as WorkflowEvent
          onEventRef.current?.(event)
        } catch {
          // Ignore malformed messages
        }
      }

      ws.onerror = () => {
        if (!cancelled) setStatus('error')
      }

      ws.onclose = () => {
        if (cancelled) return
        setStatus('disconnected')
        reconnectTimer.current = setTimeout(connect, 3000)
      }
    }

    connect()

    return () => {
      cancelled = true
      if (reconnectTimer.current) clearTimeout(reconnectTimer.current)
      wsRef.current?.close()
    }
  }, [workflowId, enabled])

  return { status }
}
