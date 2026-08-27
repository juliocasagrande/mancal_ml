import { useDatasets, useEvaluations, useModels } from '../api/hooks'
import { Card } from '../components/Card'
import { StateBoundary } from '../components/StateBoundary'
import pageStyles from './Page.module.css'
import styles from './LineagePage.module.css'

const REPO_URL = 'https://github.com/juliocasagrande/mancal_ml'

function formatDate(iso: string | null | undefined): string {
  if (!iso) return '—'
  return new Date(iso).toLocaleDateString('pt-BR')
}

export function LineagePage() {
  const datasets = useDatasets()
  const models = useModels()
  const evaluations = useEvaluations()
  const dataset = datasets.data?.[0]

  return (
    <div className={pageStyles.page}>
      <header className={pageStyles.pageHeader}>
        <h1>Linhagem e Model Card</h1>
        <p>Origem do dataset, versões de modelo, histórico de avaliações e limitações conhecidas.</p>
      </header>

      <StateBoundary isLoading={datasets.isLoading} isError={datasets.isError} error={datasets.error} isEmpty={!dataset} onRetry={() => datasets.refetch()}>
        {dataset && (
          <Card title="Dataset">
            <dl className={styles.factList}>
              <div>
                <dt>Nome</dt>
                <dd>{dataset.name}</dd>
              </div>
              <div>
                <dt>Licença</dt>
                <dd>{dataset.license}</dd>
              </div>
              <div>
                <dt>Versão / DOI</dt>
                <dd>{dataset.version}</dd>
              </div>
              <div>
                <dt>Período coberto</dt>
                <dd>
                  {formatDate(dataset.time_start)} – {formatDate(dataset.time_end)}
                </dd>
              </div>
              <div>
                <dt>Fonte</dt>
                <dd>
                  <a href={dataset.source_url} target="_blank" rel="noreferrer">
                    {dataset.source_url}
                  </a>
                </dd>
              </div>
            </dl>
          </Card>
        )}
      </StateBoundary>

      <Card title="Versões de modelo">
        <StateBoundary isLoading={models.isLoading} isError={models.isError} error={models.error} isEmpty={(models.data?.length ?? 0) === 0} onRetry={() => models.refetch()}>
          <div className={styles.tableScroll}>
            <table>
              <thead>
                <tr>
                  <th scope="col">Nome</th>
                  <th scope="col">Algoritmo</th>
                  <th scope="col">Status</th>
                  <th scope="col">Commit</th>
                  <th scope="col">Criado em</th>
                </tr>
              </thead>
              <tbody>
                {models.data?.map((m) => (
                  <tr key={m.id}>
                    <td>{m.name}</td>
                    <td>{m.algorithm}</td>
                    <td>
                      <span className={`${styles.statusPill} ${styles[m.status]}`}>{m.status}</span>
                    </td>
                    <td className={styles.mono}>{m.git_commit?.slice(0, 7) ?? '—'}</td>
                    <td>{formatDate(m.created_at)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </StateBoundary>
      </Card>

      <Card title="Histórico de avaliações">
        <StateBoundary isLoading={evaluations.isLoading} isError={evaluations.isError} error={evaluations.error} isEmpty={(evaluations.data?.length ?? 0) === 0} onRetry={() => evaluations.refetch()}>
          <ul className={styles.evalList}>
            {evaluations.data?.map((ev) => (
              <li key={ev.id}>
                <strong>{ev.model_name}</strong> — F1 {ev.metrics.f1.toFixed(3)}, PR-AUC {ev.metrics.pr_auc.toFixed(3)} ({formatDate(ev.started_at)})
              </li>
            ))}
          </ul>
        </StateBoundary>
      </Card>

      <Card title="Limitações e usos não recomendados">
        <ul className={styles.limitationsList}>
          <li>
            Não existe rótulo de falha confirmado neste dataset. As métricas usam um rótulo-proxy (baixa potência
            média por janela) — ver docs/formulacao-do-problema.md.
          </li>
          <li>Com um único evento-proxy no split de teste, a taxa de detecção de eventos tem baixíssimo poder estatístico.</li>
          <li>Este sistema é um apoio à decisão. Não deve emitir comandos para equipamentos nem ser tratado como solução certificada para operação real.</li>
          <li>Não afirma predição de vida útil remanescente nem antecedência de falha validada por especialista.</li>
          <li>
            Código e documentação completos em{' '}
            <a href={REPO_URL} target="_blank" rel="noreferrer">
              {REPO_URL}
            </a>
            .
          </li>
        </ul>
      </Card>
    </div>
  )
}
