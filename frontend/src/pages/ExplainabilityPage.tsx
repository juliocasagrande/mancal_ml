import { Bar, BarChart, CartesianGrid, Cell, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'
import { useMonitoringCurrent } from '../api/hooks'
import { Card } from '../components/Card'
import { ChartWithFallback } from '../components/ChartWithFallback'
import { StateBoundary } from '../components/StateBoundary'
import { StatusBadge } from '../components/StatusBadge'
import pageStyles from './Page.module.css'
import styles from './ExplainabilityPage.module.css'

function formatDateTime(iso: string | undefined): string {
  if (!iso) return '—'
  return new Date(iso).toLocaleString('pt-BR', { dateStyle: 'short', timeStyle: 'short' })
}

export function ExplainabilityPage() {
  const current = useMonitoringCurrent()
  const monitoring = current.data

  const contributions = monitoring?.feature_contributions ?? {}
  const chartData = Object.entries(contributions)
    .map(([channel, share]) => ({ channel, share }))
    .sort((a, b) => b.share - a.share)

  const hasDomainState = monitoring?.state === 'insufficient_data' || monitoring?.state === 'model_unavailable'
  const topChannel = chartData[0]

  return (
    <div className={pageStyles.page}>
      <header className={pageStyles.pageHeader}>
        <h1>Explicabilidade</h1>
        <p>Decomposição do score de anomalia da janela mais recente por canal, e limites da explicação.</p>
      </header>

      <div className={pageStyles.disclaimer} role="note">
        <strong>Aviso:</strong> o rótulo usado na avaliação é um <em>proxy</em> de operação atípica (baixa potência
        média), não uma falha confirmada por especialista. A contribuição por variável explica o que pesou no{' '}
        <em>score do modelo</em>, não uma causa física comprovada. Ver docs/formulacao-do-problema.md.
      </div>

      <StateBoundary
        isLoading={current.isLoading}
        isError={current.isError}
        error={current.error}
        onRetry={() => current.refetch()}
      >
        {hasDomainState ? (
          <Card title="Estado do monitoramento">
            <StatusBadge state={monitoring!.state} />
          </Card>
        ) : (
          <>
            <Card title="Janela analisada">
              <dl className={styles.factList}>
                <div>
                  <dt>Intervalo</dt>
                  <dd>
                    {formatDateTime(monitoring?.window_start)} – {formatDateTime(monitoring?.window_end)}
                  </dd>
                </div>
                <div>
                  <dt>Modelo</dt>
                  <dd>{monitoring?.model_name}</dd>
                </div>
                <div>
                  <dt>Score vs. limiar</dt>
                  <dd>
                    {monitoring?.anomaly_score?.toFixed(3)} / {monitoring?.threshold?.toFixed(3) ?? '—'}
                  </dd>
                </div>
                {topChannel && (
                  <div>
                    <dt>Canal com maior contribuição</dt>
                    <dd>
                      {topChannel.channel} ({(topChannel.share * 100).toFixed(1)}%)
                    </dd>
                  </div>
                )}
              </dl>
            </Card>

            <Card
              title="Contribuição por canal ao erro de reconstrução"
              description="Fração do erro de reconstrução do LSTM Autoencoder atribuível a cada canal (soma 1,0)."
            >
              <StateBoundary
                isLoading={false}
                isError={false}
                isEmpty={chartData.length === 0}
                emptyLabel="Este modelo não possui decomposição por variável implementada (ex.: Isolation Forest)."
              >
                <ChartWithFallback
                  title="Contribuição por canal"
                  columns={[
                    { key: 'channel', label: 'Canal' },
                    { key: 'share', label: 'Contribuição' },
                  ]}
                  rows={chartData.map((d) => ({ channel: d.channel, share: `${(d.share * 100).toFixed(1)}%` }))}
                >
                  <ResponsiveContainer width="100%" height={320}>
                    <BarChart data={chartData} layout="vertical" margin={{ left: 24 }}>
                      <CartesianGrid strokeDasharray="3 3" stroke="var(--color-border)" />
                      <XAxis type="number" tickFormatter={(v) => `${(v * 100).toFixed(0)}%`} tick={{ fontSize: 11 }} stroke="var(--color-text-faint)" />
                      <YAxis type="category" dataKey="channel" width={140} tick={{ fontSize: 11 }} stroke="var(--color-text-faint)" />
                      <Tooltip
                        formatter={(v) => `${(Number(v) * 100).toFixed(1)}%`}
                        contentStyle={{ background: 'var(--color-bg-card)', border: '1px solid var(--color-border)' }}
                      />
                      <Bar dataKey="share" isAnimationActive={false}>
                        {chartData.map((d, i) => (
                          <Cell key={d.channel} fill={i === 0 ? 'var(--color-alert)' : 'var(--color-accent)'} />
                        ))}
                      </Bar>
                    </BarChart>
                  </ResponsiveContainer>
                </ChartWithFallback>
              </StateBoundary>
            </Card>
          </>
        )}
      </StateBoundary>
    </div>
  )
}
