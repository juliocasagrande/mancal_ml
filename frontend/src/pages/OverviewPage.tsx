import { CheckCircle2 } from 'lucide-react'
import { useAcknowledgeAlert, useAlerts, useDatasetQuality, useDatasets, useMonitoringCurrent } from '../api/hooks'
import { Card } from '../components/Card'
import { StateBoundary } from '../components/StateBoundary'
import { StatusBadge } from '../components/StatusBadge'
import { HealthGauge } from '../components/HealthGauge'
import pageStyles from './Page.module.css'
import styles from './OverviewPage.module.css'

function formatDateTime(iso: string | undefined): string {
  if (!iso) return '—'
  return new Date(iso).toLocaleString('pt-BR', { dateStyle: 'short', timeStyle: 'short' })
}

export function OverviewPage() {
  const current = useMonitoringCurrent()
  const alerts = useAlerts({ acknowledged: false, limit: 5 })
  const datasets = useDatasets()
  const activeDatasetId = datasets.data?.[0]?.id
  const quality = useDatasetQuality(activeDatasetId)
  const acknowledge = useAcknowledgeAlert()

  const monitoring = current.data
  const hasDomainState = monitoring?.state === 'insufficient_data' || monitoring?.state === 'model_unavailable'

  return (
    <div className={pageStyles.page}>
      <header className={pageStyles.pageHeader}>
        <h1>Visão geral</h1>
        <p>Condição atual do mancal-guia da unidade G1, com base no modelo ativo.</p>
      </header>

      <StateBoundary
        isLoading={current.isLoading}
        isError={current.isError}
        error={current.error}
        onRetry={() => current.refetch()}
      >
        {monitoring && (
          <div aria-live="polite">
            {hasDomainState ? (
              <Card title="Estado do monitoramento">
                <div className={styles.domainState}>
                  <StatusBadge state={monitoring.state} />
                  <p>
                    {monitoring.state === 'model_unavailable'
                      ? 'Nenhum modelo ativo configurado. Ative uma versão em /api/models/{id}/activate.'
                      : 'Modelo ativo, mas ainda sem previsões suficientes para exibir o estado atual.'}
                  </p>
                </div>
              </Card>
            ) : (
              <div className={styles.grid}>
                <Card title="Índice de saúde" className={styles.healthCard}>
                  <div className={styles.healthRow}>
                    <HealthGauge value={monitoring.health_index ?? 0} />
                    <div className={styles.healthDetails}>
                      <StatusBadge state={monitoring.state} />
                      <dl className={styles.factList}>
                        <div>
                          <dt>Score de anomalia</dt>
                          <dd>
                            {monitoring.anomaly_score?.toFixed(3)}
                            {monitoring.threshold != null && (
                              <span className={styles.faint}> / limiar {monitoring.threshold.toFixed(3)}</span>
                            )}
                          </dd>
                        </div>
                        <div>
                          <dt>Última janela</dt>
                          <dd>
                            {formatDateTime(monitoring.window_start)} – {formatDateTime(monitoring.window_end)}
                          </dd>
                        </div>
                        <div>
                          <dt>Modelo ativo</dt>
                          <dd>{monitoring.model_name}</dd>
                        </div>
                      </dl>
                    </div>
                  </div>
                </Card>

                <Card title="Qualidade dos dados">
                  <StateBoundary isLoading={quality.isLoading} isError={quality.isError} error={quality.error} loadingLabel="Carregando qualidade…">
                    {quality.data ? (
                      <dl className={styles.factList}>
                        <div>
                          <dt>Status da ingestão</dt>
                          <dd>{quality.data.status}</dd>
                        </div>
                        <div>
                          <dt>Linhas processadas</dt>
                          <dd>{quality.data.row_count?.toLocaleString('pt-BR') ?? '—'}</dd>
                        </div>
                        <div>
                          <dt>Versão do pipeline</dt>
                          <dd>{quality.data.pipeline_version}</dd>
                        </div>
                      </dl>
                    ) : (
                      <p className={styles.faint}>Sem relatório de qualidade disponível.</p>
                    )}
                  </StateBoundary>
                </Card>
              </div>
            )}
          </div>
        )}
      </StateBoundary>

      <Card title="Alertas recentes não reconhecidos">
        <StateBoundary
          isLoading={alerts.isLoading}
          isError={alerts.isError}
          error={alerts.error}
          isEmpty={(alerts.data?.length ?? 0) === 0}
          emptyLabel="Nenhum alerta pendente de reconhecimento."
          onRetry={() => alerts.refetch()}
        >
          <ul className={styles.alertList}>
            {alerts.data?.map((alert) => (
              <li key={alert.id} className={styles.alertItem}>
                <StatusBadge state="alert" size="sm" />
                <div className={styles.alertBody}>
                  <p>{alert.reason}</p>
                  <span className={styles.faint}>
                    {formatDateTime(alert.window_start)} – {formatDateTime(alert.window_end)}
                  </span>
                </div>
                <button
                  type="button"
                  className={styles.ackButton}
                  onClick={() => acknowledge.mutate({ id: alert.id })}
                  disabled={acknowledge.isPending}
                >
                  <CheckCircle2 size={14} aria-hidden="true" />
                  Reconhecer
                </button>
              </li>
            ))}
          </ul>
        </StateBoundary>
      </Card>
    </div>
  )
}
