# Protocolo de avaliação (Marco 5)

Formaliza como qualquer modelo deste projeto é comparado, para que a
escolha do campeão seja reprodutível e não dependa de leitura subjetiva
de gráficos.

## 1. Split e dados

Sempre o mesmo split temporal (`docs/decisoes/0002-split-temporal-e-janelas.md`):
treino = jun/jul 2020, validação = ago/2020, teste = set/out/nov 2020.
Nenhum modelo, scaler ou limiar pode ser ajustado com dados de validação
ou teste.

## 2. Limiar de alarme

Limiar = percentil 99 da distribuição de score do próprio modelo na
**validação** (dado saudável). Mesmo critério para todos os modelos, para
que a comparação de falso-alarme seja justa.

## 3. Rótulo usado na avaliação

**Rótulo-proxy**, não um rótulo de falha confirmado — ver
`docs/formulacao-do-problema.md`. Uma janela do teste é "proxy-anômala"
se a potência média da janela for menor que 20% da mediana de potência do
treino. Isso identifica os grandes blocos de baixa atividade de
`Oct.csv`/`SEP.csv`.

**Limitação estrutural conhecida:** com este proxy, o teste contém
efetivamente **um único evento contíguo**. Isso significa que:
- `event_recall` (fração de eventos detectados) é 1,0 para qualquer
  modelo que dispare pelo menos uma vez dentro do evento — não discrimina
  entre modelos "bons" e "ótimos", apenas entre "detecta" e "não detecta".
- `detection_delay_windows` (atraso até a primeira detecção dentro do
  evento) tende a ser 0 para qualquer modelo sensível o suficiente, pelo
  mesmo motivo.
- Essas duas métricas têm, juntas, 50% do peso da matriz de decisão
  (Seção 9.4 do blueprint) mas **não discriminam os modelos neste
  dataset**. A decisão real acaba sendo tomada pelos outros 50% dos
  critérios (falso-alarme, robustez, explicabilidade, latência).

## 4. Métricas por janela

`precision`, `recall`, `f1`, `pr_auc`, `roc_auc` (quando ambas as classes
estão presentes), matriz de confusão — `app/evaluation/metrics.py::compute_window_metrics`.

## 5. Métricas por evento

Eventos = blocos contíguos de janelas rotuladas/previstas como
anômalas. `n_true_events`, `n_detected_events`, `detection_rate`,
`n_false_alarm_events`, `false_alarms_per_day` —
`app/evaluation/metrics.py::compute_event_metrics`. Atraso de detecção
via `detection_delay_windows`.

## 6. Latência

Medida com `time.perf_counter()` em 50 repetições de inferência sobre uma
única janela (não em lote), reportando p50/p95 em milissegundos —
`backend/scripts/run_decision_matrix.py::measure_latency_ms`. Todos os
valores observados até agora são sub-milissegundo a poucos milissegundos
em CPU — a latência não é, na prática, um fator decisivo neste projeto
(peso de 5% na matriz, o menor de todos).

## 7. Matriz de decisão

Seção 9.4 do blueprint, implementada em
`app/evaluation/decision_matrix.py`. Cada critério é normalizado
min-max entre os modelos comparados (não em escala absoluta), e
critérios "menor é melhor" (falso-alarme, atraso, latência) são
invertidos antes da ponderação. Um critério empatado entre todos os
modelos recebe nota máxima para todos, para não distorcer o ranking por
um empate artificial de escala.

Dois critérios (`robustness`, `explainability`) são **notas
qualitativas documentadas**, não medidas diretamente dos dados — ver a
justificativa de cada nota em `docs/resultados.md`. Isso é uma limitação
conhecida e deliberada: o blueprint pede que os pesos "sejam discutidos
como hipótese operacional", não que sejam calculados sem intervenção
humana.

## 8. Reprodução

```powershell
.\.venv\Scripts\python.exe backend\scripts\build_dataset.py
.\.venv\Scripts\python.exe backend\scripts\run_baselines.py
.\.venv\Scripts\python.exe backend\scripts\train_lstm.py
.\.venv\Scripts\python.exe backend\scripts\run_lstm_evaluation.py
.\.venv\Scripts\python.exe backend\scripts\run_decision_matrix.py
```
