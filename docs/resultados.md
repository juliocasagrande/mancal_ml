# Resultados — primeiro relatório (Marco 3)

Comparação entre um baseline estatístico e Isolation Forest, antes de
qualquer rede neural, conforme exige a Seção 15 (Marco 3) do blueprint:
"existe uma referência quantitativa antes da rede neural."

Reprodução:

```powershell
.\.venv\Scripts\python.exe backend\scripts\build_dataset.py
.\.venv\Scripts\python.exe backend\scripts\run_baselines.py
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
| `baseline_zscore` | z-score robusto (mediana/MAD) por atributo, ajustado só no treino; score = maior \|z\| entre atributos (atributos quase constantes no treino são excluídos do cálculo, não geram score espúrio) |
| `isolation_forest` | `sklearn.ensemble.IsolationForest`, 200 árvores, `random_state=42`, ajustado só no treino |

## Resultados (split de teste, contra o rótulo-proxy)

| Modelo | Precision | Recall | F1 | PR-AUC | Eventos detectados | Falso-alarmes (eventos) | Falso-alarmes/dia |
|---|---:|---:|---:|---:|---:|---:|---:|
| `baseline_zscore` | 0,954 | 1,000 | 0,976 | 1,000 | 1/1 (100%) | 6 | 0,07 |
| `isolation_forest` | 0,839 | 1,000 | 0,913 | 0,926 | 1/1 (100%) | 25 | 0,30 |

(Valores completos, incluindo matriz de confusão por janela, em
`data/interim/evaluation_report_marco3.json`, gerado a cada execução do
script — não versionado no Git.)

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

## Próximos passos (Marco 4/5)

- Introduzir a LSTM Autoencoder e comparar contra estes dois baselines
  usando o mesmo protocolo de split/limiar.
- Testar mais de uma dimensão de janela e mais de um limiar (Seção 10 do
  blueprint) antes de declarar um "campeão".
- Revisar o rótulo-proxy com mais cuidado — por exemplo, cruzando com a
  coluna `unit_speed_pct` para diferenciar "unidade parada" de "unidade
  operando com vibração anômala", que são fisicamente muito diferentes.
