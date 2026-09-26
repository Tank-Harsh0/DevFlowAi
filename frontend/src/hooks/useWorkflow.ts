import { useState, useEffect, useCallback } from 'react'
import { workflowsService } from '@/services/workflows'
import type { WorkflowRun } from '@/types/workflow'

interface UseWorkflowOptions {
  workflowId?: string
  autoRefresh?: boolean
  refreshIntervalMs?: number
}

export function useWorkflow({ workflowId, autoRefresh = false, refreshIntervalMs = 5000 }: UseWorkflowOptions = {}) {
  const [workflow, setWorkflow] = useState<WorkflowRun | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const load = useCallback(async () => {
    if (!workflowId) return
    setLoading(true)
    setError(null)
    try {
      const data = await workflowsService.get(workflowId)
      setWorkflow(data)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load workflow')
    } finally {
      setLoading(false)
    }
  }, [workflowId])

  useEffect(() => {
    void load()
  }, [load])

  useEffect(() => {
    if (!autoRefresh) return
    const id = setInterval(() => void load(), refreshIntervalMs)
    return () => clearInterval(id)
  }, [load, autoRefresh, refreshIntervalMs])

  return { workflow, loading, error, refetch: load, setWorkflow }
}
