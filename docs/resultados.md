# Resultados

Comparação entre um baseline estatístico, Isolation Forest e uma LSTM
Autoencoder, no mesmo protocolo de split/janela/limiar. A ordem de
implementação seguiu a Seção 15 do blueprint: baselines antes da rede
neural (Marco 3), rede neural depois (Marco 4) — "existe uma referência
quantitativa antes da rede neural."

Reprodução:

```powershell
.\.venv\Scripts\python.exe backend\scripts\build_dataset.py
.\.venv\Scripts\python.exe backend\scripts\run_baselines.py
.\.venv\Scripts\python.exe backend\scripts\train_lstm.py
.\.venv\Scripts\python.exe backend\scripts\run_lstm_evaluation.py
```

## Aviso obrigatório sobre o rótulo usado

**Não existe rótulo de falha confirmado neste dataset** (ver
`docs/formulacao-do-problema.md`). As métricas abaixo usam um
**rótulo-proxy**: janelas de teste com potência média abaixo de 20% da
mediana de potência do treino são marcadas como "operação atípica". Isso
captura os grandes blocos de baixa atividade observados em `Oct.csv`
(e parcialmente `SEP.csv`), mas **não confirma que a causa seja
degradação do mancal** — pode ser parada programada. Todo número de
recall/detecção abaixo mede a capacidade de detectar *esse proxy*, não
uma falha real.

## Configuração

- Split: treino = `June.csv`+`July.csv`; validação = `Aug.csv`; teste =
  `SEP.csv`+`Oct.csv`+`Nov.csv` (ver `docs/decisoes/0002-split-temporal-e-janelas.md`).
- Janela: 36 amostras (6h), passo de 6 amostras (1h).
- Atributos: mean/std/rms/peak-to-peak/skewness/kurtosis por canal
  (`feature_set_v1`), NaN/inf de janelas quase constantes tratados como 0
  (`app/features/cleaning.py`).
- Limiar de alarme: percentil 99 do score na validação (dados saudáveis),
  para ambos os modelos.

## Modelos comparados

| Modelo | Descrição |
|---|---|
| `baseline_zscore` | z-score robusto (mediana/MAD) por atributo derivado, ajustado só no treino; score = maior \|z\| entre atributos (atributos quase constantes no treino são excluídos do cálculo, não geram score espúrio) |
| `isolation_forest` | `sklearn.ensemble.IsolationForest`, 200 árvores, `random_state=42`, ajustado só no treino, sobre os mesmos atributos derivados |
| `lstm_autoencoder` | encoder/decoder LSTM (1 camada, hidden=16, latente=8), 4.499 parâmetros, treinado só com janelas saudáveis (sinal bruto normalizado, não os atributos derivados); score = erro de reconstrução (MSE) por janela; early stopping (paciência 5), 32 épocas, ~35s em CPU |

## Resultados (split de teste, contra o rótulo-proxy)

| Modelo | Precision | Recall | F1 | PR-AUC | Eventos detectados | Falso-alarmes (eventos) | Falso-alarmes/dia |
|---|---:|---:|---:|---:|---:|---:|---:|
| `baseline_zscore` | 0,954 | 1,000 | 0,976 | 1,000 | 1/1 (100%) | 6 | 0,07 |
| `isolation_forest` | 0,839 | 1,000 | 0,913 | 0,926 | 1/1 (100%) | 25 | 0,30 |
| `lstm_autoencoder` | 0,457 | 1,000 | 0,627 | 0,999 | 1/1 (100%) | 7 | 0,08 |

(Valores completos, incluindo matriz de confusão por janela e a
configuração de treino da LSTM, em
`data/interim/evaluation_report_marco3.json` e
`data/interim/evaluation_report_lstm.json`, gerados a cada execução dos
scripts — não versionados no Git.)

## Leitura dos resultados

- **Os dois modelos detectam o único evento-proxy presente no teste**
  (o grande bloco de baixa atividade de outubro). Isso era esperado: o
  proxy escolhido é um desvio extremo e fácil de separar por potência e
  vibração.
- **O baseline estatístico teve menos falso-alarmes que o Isolation
  Forest neste cenário** (6 vs. 25 eventos de falso-alarme). Isto
  contraria a suposição comum de que um modelo mais sofisticado é
  sempre melhor — com um único evento fácil de separar e atributos já
  bem comportados (estatísticas por janela, não sinal bruto de alta
  dimensão), o baseline simples generaliza melhor para o resto do teste.
- **Limitação importante:** com um único evento-proxy no teste, a
  métrica de detecção de eventos (100%) tem baixíssimo poder estatístico
  — não deve ser lida como "o modelo detecta 100% das falhas". Métricas
  por janela (F1, PR-AUC) são mais informativas aqui.
- Um bug de calibração foi corrigido durante este marco: o z-score
  ingênuo, sem tratamento de atributos quase constantes no treino,
  produzia limiares astronômicos (~10¹⁶) e um recall por janela de
  1,2% — um baseline aparentemente "quebrado" que mascarava um erro de
  implementação, não uma limitação real do método. Ver
  `docs/decisoes/` e o histórico de commits.

## Leitura dos resultados da LSTM

- A LSTM tem **PR-AUC quase idêntico ao do baseline (0,999 vs. 1,000)** —
  como *ranking* de anomalia, ela separa bem o evento-proxy do resto do
  teste, mesmo aprendendo diretamente do sinal bruto (sem os atributos
  estatísticos manuais que o baseline e o Isolation Forest usam.
- No **limiar operacional escolhido** (percentil 99 da validação), a
  LSTM tem precisão bem mais baixa (0,457) que o baseline (0,954) — ela
  sinaliza mais janelas "normais" como anômalas nesse ponto de corte
  específico. Isso é uma questão de calibração de limiar, não de
  capacidade de separação (o PR-AUC mostra que a informação está lá).
- **Neste dataset e com este proxy, o baseline estatístico simples
  continua sendo o mais competitivo em métricas operacionais**
  (precisão e falso-alarmes/dia), apesar de a LSTM ter capacidade de
  ranking equivalente. Isso ilustra exatamente o ponto da Seção 9.4 do
  blueprint: a rede neural não é escolhida por padrão — precisa provar
  vantagem operacional, e neste recorte específico (poucos meses, um
  único evento-proxy fácil de separar por potência) ela ainda não supera
  o baseline. A escolha final do campeão, com a matriz de decisão
  completa, fica para o Marco 5.

## Matriz de decisão e modelo campeão (Marco 5)

Protocolo completo em `docs/protocolo-de-avaliacao.md`. Reprodução:

```powershell
.\.venv\Scripts\python.exe backend\scripts\run_decision_matrix.py
```

Critérios qualitativos usados (não medidos diretamente — hipótese
operacional documentada):

| Modelo | Robustez (0-1) | Justificativa | Explicabilidade (0-1) | Justificativa |
|---|---:|---|---:|---|
| `baseline_zscore` | 0,5 | usa mediana/MAD fixas do treino; não se adapta a mudança de regime sem reajuste manual | 1,0 | score é literalmente o \|z\| de cada variável — o mais direto possível de explicar |
| `isolation_forest` | 0,6 | não paramétrico, tolera não linearidade, mas sensível a atributos correlacionados/redundantes | 0,4 | score de isolamento não decompõe nativamente por variável (não implementado aqui) |
| `lstm_autoencoder` | 0,7 | aprende padrões temporais não lineares; incerteza sobre generalização com apenas 2 meses de treino | 0,7 | erro de reconstrução decompõe naturalmente por canal e por instante (`app/evaluation/explainability.py`) |

### Resultado da matriz (pesos da Seção 9.4 do blueprint)

| Modelo | Score ponderado | event_recall | false_alarms/dia | atraso (janelas) | latência p95 (ms) |
|---|---:|---:|---:|---:|---:|
| `lstm_autoencoder` | **0,932** | 1,0 | 0,08 | 0 | ~1,0 |
| `baseline_zscore` | 0,900 | 1,0 | 0,07 | 0 | ~0,01 |
| `isolation_forest` | 0,550 | 1,0 | 0,30 | 0 | ~10,1 |

**Campeão declarado: `lstm_autoencoder`, por margem estreita (0,932 vs.
0,900 do baseline).**

### Por que a margem é estreita e o que isso significa

Com um único evento-proxy no teste, `event_recall` e `detection_delay`
empatam entre os três modelos (ver limitação documentada no protocolo) —
juntos, 50% do peso da matriz não discrimina nada aqui. O resultado final
é decidido pelos 50% restantes: falso-alarme e latência favorecem
claramente o baseline; robustez e explicabilidade (notas qualitativas)
favorecem a LSTM. **A escolha do campeão é sensível às notas
qualitativas atribuídas** — se `robustness`/`explainability` da LSTM
fossem 0,1 mais baixas, o baseline venceria. Isto não invalida a escolha,
mas ela deve ser lida como **uma hipótese operacional documentada, não
uma conclusão estatisticamente robusta** — o próprio blueprint pede
exatamente essa honestidade (Seção 9.4: "os pesos devem ser configuráveis
e discutidos como hipótese operacional").

Recomendação prática para uma decisão mais robusta: coletar mais meses de
dados com mais de um evento-proxy (ou, idealmente, rótulos confirmados
por um especialista de manutenção) antes de comprometer esta escolha em
produção.

## Próximos passos (Marco 6+)

- Persistir catálogo de datasets, versões de modelo e previsões no
  Railway PostgreSQL.
- Expor os três modelos e a matriz de decisão via API (FastAPI).
- Construir a interface React com as 5 páginas do blueprint, incluindo a
  Página 4 (explicabilidade) usando `app/evaluation/explainability.py`.
- Revisar o rótulo-proxy com mais cuidado — por exemplo, cruzando com a
  coluna `unit_speed_pct` para diferenciar "unidade parada" de "unidade
  operando com vibração anômala", que são fisicamente muito diferentes.
