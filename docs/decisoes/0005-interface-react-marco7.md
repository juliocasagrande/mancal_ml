# ADR 0005 — Interface React e enriquecimento de dados (Marco 7)

## Contexto

O Marco 7 (Seção 14 do blueprint) exige 5 páginas React com estados de
carregamento/erro/vazio/dados-insuficientes e acessibilidade. Ao preparar
os dados para as páginas 3 (Laboratório de modelos) e 4 (Explicabilidade),
encontrei duas lacunas que já existiam no schema/código desde os Marcos 5–6
mas nunca foram preenchidas: `PredictionRun.feature_contributions` sempre
gravado como `{}` em `populate_db.py`, e os relatórios de avaliação sem
curva precision-recall nem distribuição de score (só métricas escalares).
`app/evaluation/explainability.py` já existia desde o Marco 5 com o
comentário "Usado pela Página 4 do frontend (Marco 7)" — fechar essa
lacuna é este marco, não escopo novo.

## Decisões

- **`compute_score_curves`** (`app/evaluation/metrics.py`): calcula curva
  PR (downsample para ≤50 pontos) e histograma de score saudável×anômalo
  (25 bins) a partir dos mesmos `scores`/`labels` que os scripts de
  avaliação já calculam — nenhum modelo é retreinado.
- **`feature_contributions` real**: `populate_db.py` agora usa
  `lstm_feature_contribution` (canal LSTM é o campeão atual) para
  decompor o erro de reconstrução por variável, e
  `baseline_feature_contribution` para o baseline z-score, caso ele venha
  a ser o campeão no futuro. Isolation Forest continua com `{}` —
  `app/evaluation/explainability.py` não implementa decomposição nativa
  para ele (documentado em `docs/resultados.md`).
- **`threshold` também em `ModelVersion.hyperparameters`**, além de
  `EvaluationRun.configuration`, para o frontend expor o limiar ativo sem
  cruzar duas tabelas. Exposto em `GET /api/monitoring/current` e
  `GET /api/monitoring/timeline`, junto com `feature_contributions`.
- **Inserção em lotes com checkpoint** em `populate_db.py`: a primeira
  execução após essas mudanças falhou a meio caminho —
  `OperationalError: server closed the connection unexpectedly` — porque
  o script inseria ~2 mil `PredictionRun`/`Alert` um a um, dentro de uma
  única transação, sobre o proxy TCP do Railway (ADR 0004). Reescrito
  para gerar os IDs em Python (`uuid.uuid4()`, aproveitando que
  `PredictionRun.id` já é um default Python-side) e inserir em lotes de
  200 via `bulk_save_objects`, com `commit()` a cada lote, e um commit de
  checkpoint logo após dataset/sinal/modelos — qualquer falha de rede
  perde no máximo um lote, não a execução inteira.
- **Decomposição da matriz de decisão ponderada não foi movida para o
  Postgres.** Não há tabela para isso no schema do Marco 6 e criar uma
  seria escopo novo. A Página 3 mostra essa decomposição como conteúdo
  estático (extraído de `docs/resultados.md`), claramente rotulado como
  tal, ao lado da tabela comparativa que é dinâmica
  (`GET /api/evaluations`).

## Consequência

- `backend/scripts/run_baselines.py`, `run_lstm_evaluation.py` e
  `populate_db.py` foram reexecutados; as métricas escalares reproduzidas
  batem com `docs/resultados.md` (mesmo protocolo, nenhum retreino).
  `run_decision_matrix.py` também rodou de novo só por consistência —
  lógica inalterada, mesmo campeão (`lstm_autoencoder`, score 0,931).
- O Postgres do Railway foi apagado e recriado com os dados enriquecidos
  (23 997 amostras de sinal, 1 983 previsões, 1 623 alertas de
  demonstração — número alto de alertas é esperado: o rótulo-proxy marca
  um único bloco longo de baixa atividade em outubro, que cobre muitas
  janelas contíguas, não um evento pontual).
