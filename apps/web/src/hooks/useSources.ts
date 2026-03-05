import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { ingestionApi, sourcesApi } from '../lib/api'
import type { IngestionTriggerRequest, SourceType } from '../lib/entities'
import { useAuth } from '../store/AuthContext'

// ── Sources list ──────────────────────────────────────────────────────────────

export function useSources(params: {
  limit?: number
  offset?: number
  source_type?: SourceType
  q?: string
} = {}) {
  const { accessToken } = useAuth()
  return useQuery({
    queryKey: ['sources', params],
    queryFn: () => sourcesApi.list(accessToken!, params),
    enabled: !!accessToken,
  })
}

// ── Source detail ─────────────────────────────────────────────────────────────

export function useSource(id: string) {
  const { accessToken } = useAuth()
  return useQuery({
    queryKey: ['sources', id],
    queryFn: () => sourcesApi.get(accessToken!, id),
    enabled: !!accessToken && !!id,
  })
}

// ── Ingestion runs ────────────────────────────────────────────────────────────

export function useIngestionRuns(params: { limit?: number; offset?: number } = {}) {
  const { accessToken } = useAuth()
  return useQuery({
    queryKey: ['ingestion-runs', params],
    queryFn: () => ingestionApi.listRuns(accessToken!, params),
    enabled: !!accessToken,
  })
}

// ── Trigger ingestion ─────────────────────────────────────────────────────────

export function useTriggerIngestion() {
  const { accessToken } = useAuth()
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (data: IngestionTriggerRequest) =>
      ingestionApi.trigger(accessToken!, data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['ingestion-runs'] })
      qc.invalidateQueries({ queryKey: ['sources'] })
    },
  })
}
