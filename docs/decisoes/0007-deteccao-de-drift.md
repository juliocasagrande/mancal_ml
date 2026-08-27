# ADR 0007 — Detecção de drift de dados (extensão pós-MVP, Seção 20)

## Contexto

Seção 20 do blueprint lista "detecção de drift" como extensão possível
após o MVP. Drift mede se a distribuição dos dados de entrada mudou em
relação ao treino — um sinal complementar ao score de anomalia por
janela: um modelo pode continuar "confiante" (score baixo) mesmo operando
fora do regime em que foi treinado, se a mudança de distribuição não for
o tipo de desvio que o score de anomalia foi treinado para capturar.

## Decisões

- **Método: Population Stability Index (PSI) por atributo derivado**
  (`app/evaluation/drift.py`), não um teste estatístico como
  Kolmogorov-Smirnov — PSI é a convenção mais usada em monitoramento de
  modelos em produção, interpretável por período (um número por mês) em
  vez de um p-valor por atributo, e não exige suposição de distribuição.
  Bins = decis da distribuição de treino; PSI por atributo = soma de
  `(pct_atual - pct_treino) * ln(pct_atual/pct_treino)` por bin.
- **Limiares de severidade (`<0.1` sem drift, `0.1–0.25` moderado,
  `>=0.25` significativo)** são a heurística padrão da literatura de
  risco de crédito/ML monitoring — não recalibrados para este dataset.
  Documentado explicitamente na API e na interface (mesma disciplina do
  rótulo-proxy: nunca apresentar um número sem o limite da sua leitura).
- **Granularidade: um relatório por mês** (`source_file`), não por
  janela — PSI precisa de um batch de amostras para formar uma
  distribuição; por janela seria só ruído. `run_drift_report.py` agrupa
  `features_validation.csv`/`features_test.csv` por `source_file` e
  compara cada mês contra o treino inteiro (`features_train.csv`).
- **Atributo quase-constante no treino** (ex.: canal morto) não forma
  decis distintos — em vez de PSI explosivo ou divisão por zero, marcado
  como `severity="constante_no_treino"` com `psi=0.0`, mesma decisão de
  "não informativo" já usada no baseline z-score
  (`app/models/baseline.py`) para o mesmo problema.
- **Persistência: `Dataset.dataset_metadata["drift_report"]`**, não uma
  tabela nova nem `EvaluationRun` (que exige `model_version_id` — drift é
  propriedade dos dados, não de um modelo específico). Populado por
  `populate_db.py` de forma opcional (`drift_report.json` ausente não
  quebra o script — extensão, não requisito do MVP).
- **API: `GET /api/datasets/{id}/drift`**, 404 se o relatório não foi
  computado — espelha `/quality` (mesmo dataset, informação diferente).
- **Frontend: novo card na Página 5 (Linhagem e Model Card)**, não uma
  página nova — drift é informação de proveniência/confiabilidade do
  dataset, mesmo espírito do Model Card, não um estado operacional da
  Página 1 (o índice de saúde já cobre "o modelo está confiante agora?";
  drift responde "o regime de dados mudou desde o treino?", pergunta
  diferente e menos urgente para a visão geral).

## Achado (ver `docs/resultados.md`)

Mesmo o mês de validação (agosto, saudável) mostra drift significativo
nos canais de temperatura — evidência quantitativa de que a janela de
treino de 2 meses não cobre a variação sazonal completa. Reforça, não
contradiz, a nota qualitativa de robustez já atribuída à LSTM na matriz
de decisão do Marco 5.

## Consequência

- Reproduzir requer rodar `run_drift_report.py` antes de `populate_db.py`
  — adicionado à sequência de scripts do `README.md`.
- Com PSI tão alto em quase todo período pelos limiares padrão, o valor
  prático desta extensão está na comparação relativa entre períodos, não
  no rótulo de severidade absoluto — limitação documentada na própria
  interface, não escondida.
