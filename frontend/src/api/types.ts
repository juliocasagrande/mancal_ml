// Tipos alinhados às respostas reais da API (backend/app/api/*.py).
// Datas chegam como string ISO 8601 (FastAPI serializa datetime assim).

export type MonitoringState =
  | 'normal'
  | 'attention'
  | 'alert'
  | 'insufficient_data'
  | 'model_unavailable'

export interface Dataset {
  id: string
  name: string
  source_url: string
  license: string
  version: string
  time_start: string | null
  time_end: string | null
  metadata: Record<string, unknown>
}

export interface DatasetQuality {
  status: string
  row_count: number | null
  pipeline_version: string
  quality_report: Record<string, unknown>
}

export interface SignalPoint {
  timestamp: string
  source_file: string
  split: string
  quality_flags: { has_missing?: boolean } & Record<string, unknown>
  [channel: string]: unknown
}

export interface SignalRangeResponse {
  n_points: number
  downsample: number
  truncated: boolean
  points: SignalPoint[]
}

export interface SignalSummary {
  total_samples: number
  time_start: string | null
  time_end: string | null
  samples_by_split: Record<string, number>
  samples_by_source_file: Record<string, number>
  value_columns: string[]
}

export interface PrCurvePoint {
  precision: number
  recall: number
  threshold: number
}

export interface ScoreHistogram {
  bin_edges: number[]
  healthy: number[]
  anomalous: number[]
}

export interface ModelCurves {
  pr_curve: PrCurvePoint[]
  score_histogram: ScoreHistogram
}

export interface WindowMetrics {
  precision: number
  recall: number
  f1: number
  pr_auc: number
  roc_auc: number
  confusion_matrix: number[][]
  curves?: ModelCurves
}

export interface ModelVersion {
  id: string
  name: string
  algorithm: string
  dataset_version: string
  feature_schema: Record<string, unknown>
  hyperparameters: Record<string, unknown> & { threshold?: number }
  metrics: WindowMetrics | Record<string, unknown>
  status: 'candidate' | 'active' | 'archived'
  git_commit: string | null
  created_at: string
}

export interface MonitoringCurrent {
  state: MonitoringState
  health_index?: number
  anomaly_score?: number
  threshold?: number | null
  window_start?: string
  window_end?: string
  model_name?: string
  model_id?: string
  message?: string
  feature_contributions?: Record<string, number>
}

export interface MonitoringTimelinePoint {
  window_start: string
  window_end: string
  anomaly_score: number
  health_index: number
  state: MonitoringState
  feature_contributions: Record<string, number>
}

export interface MonitoringTimeline {
  model_name?: string
  threshold?: number | null
  state?: MonitoringState
  points: MonitoringTimelinePoint[]
}

export interface Alert {
  id: string
  prediction_run_id: string
  severity: 'attention' | 'alert'
  reason: string
  acknowledged: boolean
  acknowledged_at: string | null
  notes: string | null
  window_start: string
  window_end: string
}

export interface EvaluationRun {
  id: string
  model_version_id: string
  model_name: string
  configuration: Record<string, unknown> & { threshold?: number }
  metrics: WindowMetrics
  confusion_matrix: { matrix: number[][] }
  started_at: string
  finished_at: string | null
}
