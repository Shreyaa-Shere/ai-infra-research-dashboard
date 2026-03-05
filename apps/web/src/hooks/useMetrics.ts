import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'

import { metricsApi } from '../lib/api'
import type { MetricEntityType, MetricSeriesCreate, MetricSeriesUpdate, MetricPointsUpsertRequest } from '../lib/entities'
import { useAuth } from '../store/AuthContext'

export function useMetricsOverview() {
  const { accessToken } = useAuth()
  return useQuery({
    queryKey: ['metrics', 'overview'],
    queryFn: () => metricsApi.overview(accessToken!),
    enabled: !!accessToken,
    staleTime: 30_000,
  })
}

export function useMetricSeries(
  params: { limit?: number; offset?: number; entity_type?: MetricEntityType; entity_id?: string } = {}
) {
  const { accessToken } = useAuth()
  return useQuery({
    queryKey: ['metric-series', params],
    queryFn: () => metricsApi.listSeries(accessToken!, params),
    enabled: !!accessToken,
  })
}

export function useMetricSeriesDetail(id: string | undefined) {
  const { accessToken } = useAuth()
  return useQuery({
    queryKey: ['metric-series', id],
    queryFn: () => metricsApi.getSeries(accessToken!, id!),
    enabled: !!accessToken && !!id,
  })
}

export function useMetricPoints(
  id: string | undefined,
  params: { from_ts?: string; to_ts?: string; limit?: number } = {}
) {
  const { accessToken } = useAuth()
  return useQuery({
    queryKey: ['metric-points', id, params],
    queryFn: () => metricsApi.listPoints(accessToken!, id!, params),
    enabled: !!accessToken && !!id,
  })
}

export function useCreateMetricSeries() {
  const { accessToken } = useAuth()
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (data: MetricSeriesCreate) =>
      metricsApi.createSeries(accessToken!, data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['metric-series'] })
      qc.invalidateQueries({ queryKey: ['metrics', 'overview'] })
    },
  })
}

export function useUpdateMetricSeries(id: string) {
  const { accessToken } = useAuth()
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (data: MetricSeriesUpdate) =>
      metricsApi.updateSeries(accessToken!, id, data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['metric-series'] })
      qc.invalidateQueries({ queryKey: ['metrics', 'overview'] })
    },
  })
}

export function useDeleteMetricSeries() {
  const { accessToken } = useAuth()
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (id: string) => metricsApi.deleteSeries(accessToken!, id),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['metric-series'] })
      qc.invalidateQueries({ queryKey: ['metrics', 'overview'] })
    },
  })
}

export function useUpsertMetricPoints(id: string) {
  const { accessToken } = useAuth()
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (data: MetricPointsUpsertRequest) =>
      metricsApi.upsertPoints(accessToken!, id, data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['metric-points', id] })
      qc.invalidateQueries({ queryKey: ['metrics', 'overview'] })
    },
  })
}
