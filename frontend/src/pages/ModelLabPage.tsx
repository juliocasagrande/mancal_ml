import { CartesianGrid, Legend, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'
import { useEvaluations } from '../api/hooks'
import { Card } from '../components/Card'
import { ChartWithFallback } from '../components/ChartWithFallback'
import { StateBoundary } from '../components/StateBoundary'
import pageStyles from './Page.module.css'
import styles from './ModelLabPage.module.css'

const MODEL_COLORS: Record<string, string> = {
  baseline_zscore: '#34d399',
  isolation_forest: '#fbbf24',
  lstm_autoencoder: '#22d3ee',
}

const DECISION_MATRIX = {
  weights: {
    event_recall: 0.3,
    false_alarms_per_day: 0.25,
    detection_delay_windows: 0.2,
    robustness: 0.1,
    explainability: 0.1,
    latency_p95_ms: 0.05,
  },
  ranking: [
    { model: 'lstm_autoencoder', score: 0.932 },
    { model: 'baseline_zscore', score: 0.9 },
    { model: 'isolation_forest', score: 0.55 },
  ],
}

export function ModelLabPage() {
  const evaluations = useEvaluations()

  const prCurveData: Array<Record<string, number>> = []
  if (evaluations.data) {
    const maxPoints = Math.max(...evaluations.data.map((e) => e.metrics.curves?.pr_curve.length ?? 0))
    for (let i = 0; i < maxPoints; i++) {
      const row: Record<string, number> = { i }
      for (const ev of evaluations.data) {
        const point = ev.metrics.curves?.pr_curve[i]
        if (point) {
          row[`${ev.model_name}_recall`] = point.recall
          row[`${ev.model_name}_precision`] = point.precision
        }
      }
      prCurveData.push(row)
    }
  }

  return (
    <div className={pageStyles.page}>
      <header className={pageStyles.pageHeader}>
        <h1>Laboratório de modelos</h1>
        <p>Comparação entre baseline estatístico, Isolation Forest e LSTM Autoencoder no mesmo protocolo de split/janela/limiar.</p>
      </header>

      <StateBoundary
        isLoading={evaluations.isLoading}
        isError={evaluations.isError}
        error={evaluations.error}
        isEmpty={(evaluations.data?.length ?? 0) === 0}
        emptyLabel="Nenhuma avaliação registrada. Rode backend/scripts/run_decision_matrix.py e populate_db.py."
        onRetry={() => evaluations.refetch()}
      >
        <Card title="Métricas por janela">
          <div className={styles.tableScroll}>
            <table>
              <thead>
                <tr>
                  <th scope="col">Modelo</th>
                  <th scope="col">Precision</th>
                  <th scope="col">Recall</th>
                  <th scope="col">F1</th>
                  <th scope="col">PR-AUC</th>
                  <th scope="col">Limiar</th>
                </tr>
              </thead>
              <tbody>
                {evaluations.data?.map((ev) => (
                  <tr key={ev.id}>
                    <td>
                      <span className={styles.modelDot} style={{ background: MODEL_COLORS[ev.model_name] }} aria-hidden="true" />
                      {ev.model_name}
                    </td>
                    <td>{ev.metrics.precision.toFixed(3)}</td>
                    <td>{ev.metrics.recall.toFixed(3)}</td>
                    <td>{ev.metrics.f1.toFixed(3)}</td>
                    <td>{ev.metrics.pr_auc.toFixed(3)}</td>
                    <td>{typeof ev.configuration.threshold === 'number' ? ev.configuration.threshold.toFixed(3) : '—'}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Card>

        <Card
          title="Curva precision-recall"
          description="Uma linha por modelo (precisão por ponto amostrado da curva, calculada sobre o split de teste). Cada curva tem seu próprio grid de limiares — o eixo X é o índice do ponto amostrado, não diretamente comparável entre modelos."
        >
          <ChartWithFallback
            title="Curva precision-recall por modelo"
            columns={[{ key: 'i', label: '#' }, ...(evaluations.data ?? []).map((e) => ({ key: `${e.model_name}_precision`, label: `${e.model_name} precision` }))]}
            rows={prCurveData.map((r) => ({ i: r.i, ...r }))}
          >
            <ResponsiveContainer width="100%" height={300}>
              <LineChart data={prCurveData}>
                <CartesianGrid strokeDasharray="3 3" stroke="var(--color-border)" />
                <XAxis dataKey="i" name="ponto amostrado" tick={{ fontSize: 11 }} stroke="var(--color-text-faint)" />
                <YAxis domain={[0, 1]} tick={{ fontSize: 11 }} stroke="var(--color-text-faint)" />
                <Tooltip contentStyle={{ background: 'var(--color-bg-card)', border: '1px solid var(--color-border)' }} />
                <Legend wrapperStyle={{ fontSize: 12 }} />
                {evaluations.data?.map((ev) => (
                  <Line
                    key={ev.id}
                    type="monotone"
                    dataKey={`${ev.model_name}_precision`}
                    name={ev.model_name}
                    stroke={MODEL_COLORS[ev.model_name] ?? '#94a7c0'}
                    dot={false}
                    isAnimationActive={false}
                  />
                ))}
              </LineChart>
            </ResponsiveContainer>
          </ChartWithFallback>
        </Card>

        <div className={styles.matrixGrid}>
          {evaluations.data?.map((ev) => (
            <Card key={ev.id} title={`Matriz de confusão — ${ev.model_name}`}>
              <table className={styles.confusionTable}>
                <caption className="visually-hidden">Matriz de confusão de {ev.model_name}</caption>
                <thead>
                  <tr>
                    <th scope="col"></th>
                    <th scope="col">Previsto normal</th>
                    <th scope="col">Previsto anômalo</th>
                  </tr>
                </thead>
                <tbody>
                  <tr>
                    <th scope="row">Real normal</th>
                    <td>{ev.confusion_matrix.matrix[0][0]}</td>
                    <td>{ev.confusion_matrix.matrix[0][1]}</td>
                  </tr>
                  <tr>
                    <th scope="row">Real anômalo</th>
                    <td>{ev.confusion_matrix.matrix[1][0]}</td>
                    <td>{ev.confusion_matrix.matrix[1][1]}</td>
                  </tr>
                </tbody>
              </table>
            </Card>
          ))}
        </div>

        <Card
          title="Matriz de decisão ponderada (conteúdo estático)"
          description="Decomposição extraída de docs/resultados.md — não persistida no Postgres (ver ADR 0005). Pesos discutidos como hipótese operacional, Seção 9.4 do blueprint."
        >
          <ul className={styles.weightsList}>
            {Object.entries(DECISION_MATRIX.weights).map(([criterion, weight]) => (
              <li key={criterion}>
                {criterion}: <strong>{(weight * 100).toFixed(0)}%</strong>
              </li>
            ))}
          </ul>
          <ol className={styles.rankingList}>
            {DECISION_MATRIX.ranking.map((r) => (
              <li key={r.model}>
                {r.model} — score ponderado <strong>{r.score.toFixed(3)}</strong>
              </li>
            ))}
          </ol>
          <p className={styles.note}>
            Campeão declarado: <strong>lstm_autoencoder</strong>, por margem estreita. Com um único evento-proxy no
            split de teste, a escolha é sensível às notas qualitativas de robustez/explicabilidade — ver
            docs/resultados.md para a leitura completa.
          </p>
        </Card>
      </StateBoundary>
    </div>
  )
}
