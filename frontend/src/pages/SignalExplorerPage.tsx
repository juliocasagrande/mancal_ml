import { useMemo, useState } from 'react'
import { CartesianGrid, Legend, Line, LineChart, ReferenceArea, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'
import { useAlerts, useSignalRange, useSignalSummary } from '../api/hooks'
import { Card } from '../components/Card'
import { ChartWithFallback } from '../components/ChartWithFallback'
import { StateBoundary } from '../components/StateBoundary'
import pageStyles from './Page.module.css'
import styles from './SignalExplorerPage.module.css'

const MAX_RANGE_DAYS = 45
const DEAD_CHANNEL = 'temp_lower_guide_pad1' // canal morto documentado — excluído da seleção padrão
const CHANNEL_COLORS: Record<string, string> = {
  vibration_de: 'oklch(0.5 0.13 255)',
  vibration_nde: 'oklch(0.58 0.17 25)',
  temp_upper_guide_pad1: 'oklch(0.65 0.13 70)',
  temp_lower_guide_pad1: 'oklch(0.55 0.09 300)',
  unit_speed_pct: 'oklch(0.6 0.12 145)',
}
const FALLBACK_SERIES_COLORS = ['oklch(0.5 0.13 255)', 'oklch(0.65 0.13 70)', 'oklch(0.55 0.09 300)', 'oklch(0.6 0.12 145)', 'oklch(0.58 0.17 25)']
function colorForChannel(channel: string, index: number): string {
  return CHANNEL_COLORS[channel] ?? FALLBACK_SERIES_COLORS[index % FALLBACK_SERIES_COLORS.length]
}

function toLocalInputValue(iso: string): string {
  return new Date(iso).toISOString().slice(0, 16)
}

export function SignalExplorerPage() {
  const summary = useSignalSummary()
  const [range, setRange] = useState<{ start: string; end: string } | null>(null)
  const [downsample, setDownsample] = useState(5)
  const [selectedChannels, setSelectedChannels] = useState<string[] | null>(null)

  const summaryData = summary.data
  const defaultRange = useMemo(() => {
    if (!summaryData?.time_end) return null
    const end = new Date(summaryData.time_end)
    const start = new Date(end)
    start.setDate(start.getDate() - 7)
    return { start: start.toISOString(), end: end.toISOString() }
  }, [summaryData])

  const effectiveRange = range ?? defaultRange
  const signalRange = useSignalRange(effectiveRange?.start, effectiveRange?.end, downsample)
  const alerts = useAlerts({ limit: 200 })

  const channels = summary.data?.value_columns ?? []
  const activeChannels = selectedChannels ?? channels.filter((c) => c !== DEAD_CHANNEL).slice(0, 3)

  const chartData = (signalRange.data?.points ?? []).map((p) => ({
    timestamp: p.timestamp,
    timestampMs: new Date(p.timestamp).getTime(),
    label: new Date(p.timestamp).toLocaleString('pt-BR', { dateStyle: 'short', timeStyle: 'short' }),
    split: p.split,
    hasMissing: p.quality_flags?.has_missing,
    ...Object.fromEntries(activeChannels.map((c) => [c, p[c]])),
  }))

  const alertRegions = (alerts.data ?? [])
    .map((a) => ({ id: a.id, x1: new Date(a.window_start).getTime(), x2: new Date(a.window_end).getTime() }))
    .filter((r) => chartData.some((d) => d.timestampMs >= r.x1 && d.timestampMs <= r.x2))

  const SPLIT_COLORS: Record<string, string> = { train: 'var(--color-normal)', validation: 'var(--color-neutral)', test: 'var(--color-accent)' }
  const splitRegions: Array<{ split: string; x1: number; x2: number }> = []
  for (const point of chartData) {
    const lastRegion = splitRegions.at(-1)
    if (lastRegion && lastRegion.split === point.split) {
      lastRegion.x2 = point.timestampMs
    } else {
      splitRegions.push({ split: point.split, x1: point.timestampMs, x2: point.timestampMs })
    }
  }

  function handleRangeChange(field: 'start' | 'end', value: string) {
    const base = effectiveRange ?? { start: value, end: value }
    const next = { ...base, [field]: new Date(value).toISOString() }
    const days = (new Date(next.end).getTime() - new Date(next.start).getTime()) / 86_400_000
    if (days > MAX_RANGE_DAYS) return // limite da API (Seção 17 do blueprint)
    setRange(next)
  }

  return (
    <div className={pageStyles.page}>
      <header className={pageStyles.pageHeader}>
        <h1>Explorador de sinais</h1>
        <p>Sinal bruto/limpo por canal, com regiões de treino/validação/teste e alertas marcados. Intervalo máximo de {MAX_RANGE_DAYS} dias por consulta.</p>
      </header>

      <StateBoundary isLoading={summary.isLoading} isError={summary.isError} error={summary.error} onRetry={() => summary.refetch()}>
        <Card title="Período e canais">
          <div className={pageStyles.toolbar}>
            <label className={pageStyles.field}>
              Início
              <input
                type="datetime-local"
                value={effectiveRange ? toLocalInputValue(effectiveRange.start) : ''}
                onChange={(e) => handleRangeChange('start', e.target.value)}
              />
            </label>
            <label className={pageStyles.field}>
              Fim
              <input
                type="datetime-local"
                value={effectiveRange ? toLocalInputValue(effectiveRange.end) : ''}
                onChange={(e) => handleRangeChange('end', e.target.value)}
              />
            </label>
            <label className={pageStyles.field}>
              Downsample (1 a cada N)
              <input
                type="number"
                min={1}
                max={1000}
                value={downsample}
                onChange={(e) => setDownsample(Number(e.target.value) || 1)}
              />
            </label>
          </div>
          <fieldset className={styles.channelFieldset}>
            <legend>Canais exibidos</legend>
            {channels.map((c) => (
              <label key={c} className={styles.channelOption}>
                <input
                  type="checkbox"
                  checked={activeChannels.includes(c)}
                  onChange={(e) => {
                    const base = selectedChannels ?? activeChannels
                    setSelectedChannels(e.target.checked ? [...base, c] : base.filter((x) => x !== c))
                  }}
                />
                {c}
                {c === DEAD_CHANNEL && <span className={styles.deadTag}>canal morto</span>}
              </label>
            ))}
          </fieldset>
        </Card>
      </StateBoundary>

      <Card title="Série temporal">
        <StateBoundary
          isLoading={signalRange.isLoading}
          isError={signalRange.isError}
          error={signalRange.error}
          isEmpty={chartData.length === 0}
          emptyLabel="Nenhum ponto no intervalo selecionado."
          onRetry={() => signalRange.refetch()}
        >
          {signalRange.data?.truncated && (
            <p className={styles.truncatedNote}>Resultado truncado — reduza o intervalo ou aumente o downsample.</p>
          )}
          <ChartWithFallback
            title="Série temporal dos canais selecionados"
            columns={[{ key: 'label', label: 'Instante' }, ...activeChannels.map((c) => ({ key: c, label: c }))]}
            rows={chartData.map((row) => {
              const record = row as unknown as Record<string, string | number | undefined>
              return { label: row.label, ...Object.fromEntries(activeChannels.map((c) => [c, record[c] ?? '—'])) }
            })}
          >
            <ResponsiveContainer width="100%" height={360}>
              <LineChart data={chartData}>
                <CartesianGrid strokeDasharray="3 3" stroke="var(--color-border)" />
                <XAxis
                  dataKey="timestampMs"
                  type="number"
                  domain={['dataMin', 'dataMax']}
                  tickFormatter={(ms) => new Date(ms).toLocaleString('pt-BR', { dateStyle: 'short', timeStyle: 'short' })}
                  tick={{ fontSize: 11 }}
                  minTickGap={60}
                  stroke="var(--color-text-faint)"
                />
                <YAxis tick={{ fontSize: 11 }} stroke="var(--color-text-faint)" />
                <Tooltip
                  labelFormatter={(ms) => new Date(ms as number).toLocaleString('pt-BR', { dateStyle: 'short', timeStyle: 'short' })}
                  contentStyle={{ background: 'var(--color-bg-card)', border: '1px solid var(--color-border)' }}
                />
                <Legend wrapperStyle={{ fontSize: 12 }} />
                {splitRegions.map((r, i) => (
                  <ReferenceArea key={i} x1={r.x1} x2={r.x2} fill={SPLIT_COLORS[r.split] ?? 'transparent'} fillOpacity={0.05} ifOverflow="hidden" />
                ))}
                {alertRegions.map((r) => (
                  <ReferenceArea key={r.id} x1={r.x1} x2={r.x2} fill="var(--color-alert)" fillOpacity={0.12} ifOverflow="hidden" />
                ))}
                {activeChannels.map((c, i) => (
                  <Line
                    key={c}
                    type="monotone"
                    dataKey={c}
                    stroke={colorForChannel(c, i)}
                    dot={false}
                    isAnimationActive={false}
                    connectNulls
                  />
                ))}
              </LineChart>
            </ResponsiveContainer>
            <p className={styles.legendNote}>
              Fundo verde/violeta/azul-grafite = região de treino/validação/teste. Fundo vermelho = janela com alerta.
            </p>
          </ChartWithFallback>
        </StateBoundary>
      </Card>
    </div>
  )
}
