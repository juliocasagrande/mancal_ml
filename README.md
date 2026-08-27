# hydro-bearing-predictive-maintenance

## Problema operacional

Mancais-guia de turbinas hidráulicas degradam de forma silenciosa até que
a vibração ultrapasse um limiar que já compromete a operação. Detectar
esse desvio de condição cedo, contra falsos alarmes que custam
manutenção desnecessária, é o problema central da manutenção preditiva
de ativos hidrelétricos.

## Resultado principal

Comparando um baseline estatístico, Isolation Forest e uma LSTM
Autoencoder sobre 6 meses de vibração real do mancal-guia da Unidade 01,
o modelo campeão (LSTM Autoencoder) detecta o único período de operação
atípica do split de teste com **falso-alarme de 0,08 evento/dia**, contra
0,07 do baseline e 0,30 do Isolation Forest — mas venceu por **margem
estreita** (0,932 vs. 0,900 do baseline na matriz de decisão ponderada),
não por vantagem esmagadora. Ver `docs/resultados.md` para a leitura
completa, incluindo por que essa margem é sensível às notas qualitativas
atribuídas.

## Demonstração

**API:** <https://backend-production-329c9.up.railway.app/docs>
**Interface:** <https://frontend-zeta-ten-m6tiwls3qo.vercel.app>

(Publicação opcional — ver `docs/decisoes/0006-publicacao-marco9.md`. Se
os links acima estiverem fora do ar, rodar localmente conforme a seção
"Executar localmente" abaixo.)

![Visão geral — índice de saúde em estado de alerta](docs/img/01-visao-geral.png)

![Laboratório de modelos — comparação e curva PR](docs/img/03-laboratorio-modelos.png)

Roteiro de demonstração completo (5 minutos, 5 páginas) em
[`docs/roteiro-demonstracao.md`](docs/roteiro-demonstracao.md).

## Arquitetura

```mermaid
flowchart LR
    A[Dataset público] --> B[Validação e catálogo]
    B --> C[Limpeza e resampling]
    C --> D[Janelas temporais]
    D --> E1[Baseline estatístico]
    D --> E2[ML clássico]
    D --> E3[LSTM Autoencoder]
    E1 --> F[Avaliação temporal]
    E2 --> F
    E3 --> F
    F --> G[Registro do modelo campeão]
    G --> H[FastAPI · Railway]
    H --> I[React Control Room · Vercel]
    H --> J[(Railway PostgreSQL)]
```

Treino e inferência são módulos separados; o frontend nunca acessa o
banco diretamente; toda previsão informa versão do modelo e instante dos
dados; nenhum alerta gera atuação automática. Ver
[`PROJETO_01_MANUTENCAO_PREDITIVA_UHE.md`](PROJETO_01_MANUTENCAO_PREDITIVA_UHE.md)
para o blueprint completo e `docs/decisoes/` para as decisões de
implementação de cada marco.

## Dataset, licença e limitações

**Bearing Vibration Dataset of a Hydropower Project** (Yasir Saleem
Afridi, [DOI 10.6084/m9.figshare.21290895.v1](https://doi.org/10.6084/m9.figshare.21290895.v1),
CC BY 4.0). 6 meses (jun–nov/2020) de vibração e temperatura do
mancal-guia da turbina da Unidade 01, de uma UHE de 969 MW. Detalhes,
hashes e achados da auditoria em [`data/README.md`](data/README.md) e
`docs/dicionario-de-dados.md`.

**Limitação central, repetida em todo o projeto porque é a mais
importante:** o dataset **não tem rótulo de falha confirmado**. As
métricas de detecção usam um rótulo-proxy (janelas de baixa potência
média) que captura os blocos de baixa atividade observados em
`Oct.csv`/`SEP.csv`, mas não confirma que a causa seja degradação do
mancal — pode ser parada programada. Ver
`docs/formulacao-do-problema.md` para a análise completa.

## Formulação do problema

Sem rótulo confiável nem transição de falha temporalmente identificável,
a tarefa formalizada é **detecção não supervisionada de anomalias/desvio
de condição** (não classificação saudável×falha, nem prognóstico de vida
útil remanescente) — opção 1 da Seção 3 do blueprint, a única sustentada
pelos dados. Justificativa completa em
[`docs/formulacao-do-problema.md`](docs/formulacao-do-problema.md).

## Protocolo temporal e prevenção de vazamento

- Treino: `June.csv` + `July.csv` (mais antigo, saudável).
- Validação: `Aug.csv` — usada para escolher limiar e hiperparâmetros.
- Teste: `SEP.csv` + `Oct.csv` + `Nov.csv` — nunca tocado até a avaliação
  final, contém os blocos de operação atípica.
- Janelas sobrepostas não atravessam fronteiras de mês nem de split;
  scalers ajustados exclusivamente no treino. Testes de vazamento e
  fronteiras em `backend/tests/`. Decisão completa em
  `docs/decisoes/0002-split-temporal-e-janelas.md`.

## Modelos comparados

| Modelo | Descrição |
|---|---|
| `baseline_zscore` | z-score robusto (mediana/MAD) por atributo derivado |
| `isolation_forest` | `sklearn.ensemble.IsolationForest`, 200 árvores |
| `lstm_autoencoder` | encoder/decoder LSTM (1 camada, 4.499 parâmetros), treinada só em janelas saudáveis, score = erro de reconstrução |

A rede neural foi tratada como hipótese a testar contra os métodos mais
simples, nunca como escolha padrão — Seção 9.4 do blueprint.

## Métricas e resultados

| Modelo | Precision | Recall | F1 | PR-AUC | Falso-alarme/dia |
|---|---:|---:|---:|---:|---:|
| `baseline_zscore` | 0,954 | 1,000 | 0,976 | 1,000 | 0,07 |
| `isolation_forest` | 0,839 | 1,000 | 0,913 | 0,926 | 0,30 |
| `lstm_autoencoder` | 0,457 | 1,000 | 0,627 | 0,999 | 0,08 |

**Campeão declarado: `lstm_autoencoder`**, por margem estreita na matriz
de decisão ponderada (0,932 vs. 0,900 do baseline) — favorecido por
robustez e explicabilidade qualitativas, apesar de falso-alarme e
latência favorecerem o baseline. Com um único evento-proxy no teste,
`event_recall` e `detection_delay` empatam entre os três modelos e não
discriminam a escolha. Leitura completa, incluindo por que a margem é
sensível às notas atribuídas, em [`docs/resultados.md`](docs/resultados.md)
e o protocolo formal em [`docs/protocolo-de-avaliacao.md`](docs/protocolo-de-avaliacao.md).

## Explicabilidade

A Página 4 da interface decompõe o erro de reconstrução da LSTM por
variável (canal com maior contribuição, comparação com o envelope
saudável) e reafirma o aviso de rótulo-proxy: a contribuição explica o
que pesou no *score* do modelo, não uma causa física comprovada.
Implementado em `backend/app/evaluation/explainability.py`.

![Explicabilidade — contribuição por canal](docs/img/04-explicabilidade.png)

## Executar localmente (Windows, sem admin, sem Docker)

```powershell
python --version
node --version
npm --version
git --version
```

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -r backend\requirements.txt
```

Se o caminho do projeto for longo (ex.: dentro do OneDrive), a instalação
do `torch` pode falhar com `WinError 206` — ver
`docs/decisoes/0003-instalacao-pytorch-caminho-longo.md`.

```powershell
cd frontend
npm install
```

### Pipeline de dados e modelos

```powershell
.\.venv\Scripts\python.exe backend\scripts\download_dataset.py
.\.venv\Scripts\python.exe backend\scripts\audit_dataset.py
.\.venv\Scripts\python.exe backend\scripts\build_dataset.py
.\.venv\Scripts\python.exe backend\scripts\run_baselines.py
.\.venv\Scripts\python.exe backend\scripts\train_lstm.py --config configs\lstm_autoencoder.yaml
.\.venv\Scripts\python.exe backend\scripts\run_lstm_evaluation.py
.\.venv\Scripts\python.exe backend\scripts\run_decision_matrix.py
.\.venv\Scripts\python.exe backend\scripts\run_drift_report.py
```

### Banco de dados e API

Requer um Postgres acessível via `DATABASE_URL` no `.env` (local ou
Railway — ver `docs/decisoes/0004-railway-postgres-e-api.md`).

```powershell
cd backend
..\.venv\Scripts\python.exe -m alembic upgrade head
cd ..
.\.venv\Scripts\python.exe backend\scripts\populate_db.py
.\.venv\Scripts\python.exe -m uvicorn app.main:app --app-dir backend --port 8000
```

Documentação interativa em `http://localhost:8000/docs`.

### Frontend

```powershell
cd frontend
npm run dev
```

Por padrão aponta para `http://localhost:8000`; para apontar para outra
API, definir `VITE_API_BASE_URL` (ver `frontend/src/api/client.ts`).

## Variáveis de ambiente

```dotenv
DATABASE_URL=postgresql+psycopg://USER:PASSWORD@HOST:PORT/DB?sslmode=require
MODEL_ARTIFACT_DIR=artifacts
APP_ENV=development
CORS_ORIGINS=http://localhost:5173
```

```dotenv
# frontend/.env.production (ou .env.local)
VITE_API_BASE_URL=http://localhost:8000
```

Nunca versionar `.env`; `DATABASE_URL` nunca é enviada ao frontend.

## Testes

```powershell
.\.venv\Scripts\python.exe -m pytest backend\tests -q
cd frontend; npm run test -- --run
```

CI no GitHub Actions (`.github/workflows/ci.yml`) roda lint, tipos,
testes e build em cada push/PR para `master`.

## Estrutura do repositório

Árvore completa em
[`PROJETO_01_MANUTENCAO_PREDITIVA_UHE.md`](PROJETO_01_MANUTENCAO_PREDITIVA_UHE.md).
Documentação de progresso e decisões técnicas em [`docs/`](docs/),
incluindo um ADR por marco em `docs/decisoes/`.

## Usos não recomendados

- Não é um sistema certificado para operação real nem emite comandos
  para equipamentos — é apoio à decisão.
- Não afirma "predição de vida útil remanescente" nem "detecção com X
  dias de antecedência de falha confirmada" — não há rótulo de falha
  neste dataset (ver `docs/formulacao-do-problema.md`).
- Os limiares de alarme são experimentais, calibrados em 2 meses de
  dado saudável de uma única unidade — não devem ser promovidos a
  produção sem revisão por um especialista de confiabilidade e mais
  histórico de eventos reais.
- Não usa a marca CTG como se fosse produto oficial da companhia.

## Próximos passos

- Coletar mais meses de dados com mais de um evento-proxy, ou obter
  rótulos confirmados por especialista, antes de comprometer a escolha
  do modelo campeão em um cenário real.
- Cruzar `unit_speed_pct` com os blocos de baixa atividade para
  diferenciar "unidade parada" de "unidade operando com vibração
  anômala" (ver `docs/formulacao-do-problema.md`).
- Extensões possíveis, apenas após validação do MVP: 1D-CNN Autoencoder,
  SHAP para o modelo clássico, simulação de streaming, autenticação na
  API. Detecção de drift já implementada (`docs/decisoes/0007-deteccao-de-drift.md`).

## Licença

Código sob licença MIT (ver `LICENSE`). Dataset sob CC BY 4.0 — ver
`data/README.md` e `CITATION.cff` para atribuição correta.
