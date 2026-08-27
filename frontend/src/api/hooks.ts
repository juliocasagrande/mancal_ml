import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { apiGet, apiPatch } from './client'
import type {
  Alert,
  Dataset,
  DatasetQuality,
  DriftReport,
  EvaluationRun,
  ModelVersion,
  MonitoringCurrent,
  MonitoringTimeline,
  SignalRangeResponse,
  SignalSummary,
} from './types'

const MONITORING_POLL_MS = 30_000

export function useDatasets() {
  return useQuery({ queryKey: ['datasets'], queryFn: () => apiGet<Dataset[]>('/api/datasets') })
}

export function useDatasetQuality(datasetId: string | undefined) {
  return useQuery({
    queryKey: ['dataset-quality', datasetId],
    queryFn: () => apiGet<DatasetQuality>(`/api/datasets/${datasetId}/quality`),
    enabled: Boolean(datasetId),
  })
}

export function useDatasetDrift(datasetId: string | undefined) {
  return useQuery({
    queryKey: ['dataset-drift', datasetId],
    queryFn: () => apiGet<DriftReport>(`/api/datasets/${datasetId}/drift`),
    enabled: Boolean(datasetId),
    retry: false, // 404 é esperado para datasets sem relatório de drift computado
  })
}

export function useSignalSummary() {
  return useQuery({ queryKey: ['signal-summary'], queryFn: () => apiGet<SignalSummary>('/api/signals/summary') })
}

export function useSignalRange(start: string | undefined, end: string | undefined, downsample: number) {
  return useQuery({
    queryKey: ['signal-range', start, end, downsample],
    queryFn: () => apiGet<SignalRangeResponse>('/api/signals/range', { start, end, downsample }),
    enabled: Boolean(start && end),
  })
}

export function useModels() {
  return useQuery({ queryKey: ['models'], queryFn: () => apiGet<ModelVersion[]>('/api/models') })
}

export function useModel(modelId: string | undefined) {
  return useQuery({
    queryKey: ['model', modelId],
    queryFn: () => apiGet<ModelVersion>(`/api/models/${modelId}`),
    enabled: Boolean(modelId),
  })
}

export function useMonitoringCurrent() {
  return useQuery({
    queryKey: ['monitoring-current'],
    queryFn: () => apiGet<MonitoringCurrent>('/api/monitoring/current'),
    refetchInterval: MONITORING_POLL_MS,
  })
}

export function useMonitoringTimeline(start?: string, end?: string) {
  return useQuery({
    queryKey: ['monitoring-timeline', start, end],
    queryFn: () => apiGet<MonitoringTimeline>('/api/monitoring/timeline', { start, end }),
  })
}

export function useAlerts(params: { acknowledged?: boolean; limit?: number } = {}) {
  return useQuery({
    queryKey: ['alerts', params.acknowledged, params.limit],
    queryFn: () =>
      apiGet<Alert[]>('/api/alerts', {
        acknowledged: params.acknowledged === undefined ? undefined : String(params.acknowledged),
        limit: params.limit,
      }),
  })
}

export function useAcknowledgeAlert() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({ id, notes }: { id: string; notes?: string }) =>
      apiPatch<Alert>(`/api/alerts/${id}`, { acknowledged: true, ...(notes ? { notes } : {}) }),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ['alerts'] })
    },
  })
}

export function useEvaluations() {
  return useQuery({ queryKey: ['evaluations'], queryFn: () => apiGet<EvaluationRun[]>('/api/evaluations') })
}
