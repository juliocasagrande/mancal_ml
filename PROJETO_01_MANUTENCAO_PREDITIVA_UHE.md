# Blueprint de implementação — Manutenção preditiva em unidade geradora hidrelétrica

## 1. Propósito

Construir um sistema público e reproduzível de detecção antecipada de degradação em mancal-guia de turbina hidráulica. O projeto deve demonstrar domínio de:

- engenharia de dados de séries temporais industriais;
- análise de desempenho e confiabilidade de ativos;
- comparação entre métodos estatísticos, Machine Learning clássico e rede neural;
- avaliação orientada à operação, com atenção a falsos alarmes e antecedência da detecção;
- disponibilização do modelo em uma aplicação React profissional;
- rastreabilidade de dados, modelos, experimentos e previsões.

Nome sugerido do repositório: `hydro-bearing-predictive-maintenance`.

Frase de apresentação:

> Sistema de monitoramento de condição que compara baselines estatísticos, modelos clássicos e uma rede LSTM para detectar degradação em um mancal de turbina hidráulica, com avaliação temporal, índice de saúde e explicabilidade operacional.

O sistema é um apoio à decisão. Não deve emitir comandos para equipamentos nem se apresentar como solução certificada para operação real.

---

## 2. Relação com a vaga

| Demanda profissional | Evidência criada pelo projeto |
|---|---|
| Modelos de IA e ML para manutenção preditiva | Rede neural aplicada a dados reais de condição de um ativo hidrelétrico |
| Análises de desempenho, confiabilidade e risco técnico | Índice de saúde, detecção de anomalias, alarmes e análise de falsos positivos |
| Integração de dados operacionais | Pipeline completo de ingestão, validação, transformação, treino e inferência |
| Implantação de novas tecnologias | API versionada, interface operacional e processo reproduzível de publicação do modelo |
| Decisão baseada em dados | Comparação quantitativa de modelos e limiares, sem escolher rede neural por preferência |
| Rastreabilidade | Linhagem do dataset, versão do modelo, configuração, métricas e histórico de previsões |

---

## 3. Dataset e limites da afirmação

Dataset principal:

- **Bearing Vibration Dataset of a Hydropower Project**;
- 12 meses de dados de vibração obtidos do SCADA;
- usina hidrelétrica de 969 MW, com quatro unidades de 242,25 MW;
- dados do mancal-guia da turbina da Unidade 01;
- presença de períodos saudáveis e associados à falha;
- licença CC BY 4.0.

Fonte: <https://figshare.com/articles/dataset/Bearing_Vibration_Dataset_of_a_Hydropower_Project/21290895>

Registrar no repositório:

- URL, DOI, autores, licença e data do download;
- hash SHA-256 de cada arquivo original;
- dicionário de dados produzido após inspeção;
- limitações conhecidas e campos cuja interpretação não esteja documentada.

Não afirmar “predição de vida útil remanescente” ou “detecção com X dias de antecedência” antes de verificar se os rótulos e a cronologia permitem essa conclusão. Após a auditoria do dataset, formalizar uma das tarefas:

1. **detecção não supervisionada de anomalias**, se houver pouco rótulo;
2. **classificação temporal saudável × falha**, se os rótulos forem confiáveis;
3. **prognóstico/antecedência**, somente se a transição para falha for temporalmente identificável.

---

## 4. Restrições do ambiente

O projeto deve funcionar em Windows sem permissão de administrador e sem Docker.

- Instalar Python somente em ambiente virtual do projeto.
- Instalar dependências Node somente com `npm install` dentro do repositório.
- Não usar `npm install -g`.
- Não exigir PostgreSQL local, WSL, CUDA, compiladores C/C++ ou serviços do Windows.
- Utilizar wheels binários compatíveis com Windows.
- Treino local em CPU deve ser possível; Google Colab pode ser usado opcionalmente para acelerar experimentos.
- O banco PostgreSQL ficará no Railway.
- O sistema deve continuar demonstrável localmente mesmo se o frontend ou a API ainda não estiverem publicados.

Auditoria inicial:

```powershell
python --version
python -c "import struct; print(struct.calcsize('P') * 8)"
node --version
npm --version
git --version
```

Se `python` não funcionar, testar `py`. Preferir Python 3.11 ou 3.12 em 64 bits.

Ambiente virtual sem depender de ativação:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -r backend\requirements.txt
```

---

## 5. Stack decidida

### Backend e Machine Learning

- Python 3.11/3.12;
- FastAPI e Uvicorn;
- Pydantic e `pydantic-settings`;
- Pandas, NumPy e SciPy;
- scikit-learn;
- PyTorch CPU para a LSTM Autoencoder;
- SQLAlchemy 2;
- Psycopg 3 com distribuição binária;
- Alembic para migrações;
- Joblib para artefatos clássicos;
- Pytest, Ruff e MyPy;
- Matplotlib apenas para relatórios estáticos de pesquisa.

Evitar bibliotecas de AutoML. O objetivo é tornar o pipeline e as decisões visíveis.

### Frontend

- React + TypeScript + Vite;
- React Router;
- TanStack Query;
- Recharts;
- Framer Motion para animações discretas;
- Lucide React para ícones;
- CSS Modules ou CSS próprio com variáveis de tema;
- Vitest + React Testing Library.

### Banco e hospedagem

- PostgreSQL no Railway;
- frontend local e, opcionalmente, Vercel;
- API local e, opcionalmente, Railway via build automático do repositório;
- nenhuma imagem Docker criada localmente.

O banco guarda metadados, resultados e séries necessárias à demonstração. Os arquivos brutos permanecem em `data/raw/`, fora do Git quando a licença ou o tamanho exigir, e são obtidos por script documentado.

---

## 6. Arquitetura

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
    G --> H[FastAPI]
    H --> I[React Control Room]
    H --> J[(Railway PostgreSQL)]
```

Princípios:

- treino e inferência são módulos separados;
- todo transformador ajustado no treino é persistido junto ao modelo;
- o frontend nunca acessa o banco diretamente;
- toda previsão informa versão do modelo e instante dos dados;
- nenhum alerta gera atuação automática.

---

## 7. Estrutura sugerida do repositório

```text
hydro-bearing-predictive-maintenance/
├── README.md
├── LICENSE
├── CITATION.cff
├── .gitignore
├── .env.example
├── data/
│   ├── README.md
│   ├── raw/.gitkeep
│   ├── interim/.gitkeep
│   └── processed/.gitkeep
├── docs/
│   ├── arquitetura.md
│   ├── dicionario-de-dados.md
│   ├── protocolo-de-avaliacao.md
│   ├── resultados.md
│   ├── modelo-de-ameacas.md
│   └── decisoes/
├── notebooks/
│   ├── 01_auditoria_dataset.ipynb
│   ├── 02_analise_exploratoria.ipynb
│   └── 03_experimentos_iniciais.ipynb
├── backend/
│   ├── requirements.in
│   ├── requirements.txt
│   ├── alembic.ini
│   ├── migrations/
│   ├── app/
│   │   ├── main.py
│   │   ├── api/
│   │   ├── core/
│   │   ├── db/
│   │   ├── ingestion/
│   │   ├── features/
│   │   ├── models/
│   │   ├── training/
│   │   ├── inference/
│   │   └── evaluation/
│   ├── scripts/
│   └── tests/
├── frontend/
│   ├── package.json
│   ├── vite.config.ts
│   └── src/
│       ├── api/
│       ├── components/
│       ├── features/
│       ├── pages/
│       ├── styles/
│       └── types/
└── artifacts/
    ├── README.md
    └── .gitkeep
```

Notebooks servem à exploração; o pipeline final deve residir em módulos Python testáveis.

---

## 8. Tratamento dos dados

### 8.1 Contrato de ingestão

Cada execução deve registrar:

- `dataset_version`;
- hash dos arquivos;
- intervalo temporal;
- número de linhas;
- colunas e unidades;
- frequência nominal e frequência observada;
- valores ausentes, duplicados e fora de ordem;
- regras aplicadas;
- versão do código.

O pipeline deve:

1. preservar os arquivos originais como somente leitura;
2. normalizar nomes e tipos sem alterar o bruto;
3. ordenar por tempo e identificar duplicidades;
4. detectar gaps e mudanças de frequência;
5. aplicar resampling somente com justificativa;
6. marcar dados imputados em coluna própria;
7. gerar um relatório de qualidade antes do treino.

### 8.2 Divisão temporal

Nunca usar divisão aleatória convencional em séries temporais.

- treino: trecho saudável mais antigo;
- validação: trecho saudável posterior, usado para hiperparâmetros e limiar;
- teste: período futuro mantido intocado, incluindo a degradação/falha quando disponível.

Janelas sobrepostas não podem atravessar as fronteiras entre treino, validação e teste. Scalers devem ser ajustados exclusivamente no treino.

### 8.3 Engenharia de atributos

Começar com sinais brutos e acrescentar, de forma versionada:

- médias e desvios móveis;
- RMS;
- amplitude pico a pico;
- assimetria e curtose;
- tendência local;
- derivadas temporais;
- energia por janela;
- atributos de frequência, somente se a amostragem justificar FFT;
- regime de carga ou sazonalidade, caso existam variáveis adequadas.

Não produzir dezenas de atributos sem ablação. Cada grupo deve ser comparado ao baseline.

---

## 9. Experimentos de modelagem

### 9.1 Baseline operacional

- limite fixo documentado, se houver referência;
- z-score robusto;
- EWMA/CUSUM;
- limiar por percentil da validação saudável.

### 9.2 Machine Learning clássico

- Isolation Forest para anomalia não supervisionada;
- Logistic Regression e Random Forest se houver rótulos confiáveis;
- Gradient Boosting opcional, desde que instalado por wheel e justificado.

### 9.3 Rede neural principal

Implementar uma **LSTM Autoencoder**:

- entrada: janela temporal normalizada;
- encoder: uma ou duas camadas LSTM pequenas;
- vetor latente;
- decoder que reconstrói a janela;
- loss inicial: MSE ou Huber;
- treino somente em condição saudável;
- score de anomalia: erro de reconstrução agregado;
- limiar escolhido na validação saudável;
- seed fixa e early stopping.

Manter a rede pequena para CPU. Registrar número de parâmetros, tempo de treino e memória. Uma 1D-CNN Autoencoder pode ser extensão comparativa, não requisito do MVP.

### 9.4 Escolha do modelo campeão

O campeão não é automaticamente a rede neural. Usar uma matriz:

| Critério | Peso sugerido |
|---|---:|
| Recall de eventos de falha/degradação | 30% |
| Falsos alarmes por unidade de tempo | 25% |
| Antecedência da detecção | 20% |
| Robustez entre regimes | 10% |
| Explicabilidade | 10% |
| Latência de inferência | 5% |

Os pesos devem ser configuráveis e discutidos como hipótese operacional.

---

## 10. Avaliação obrigatória

### Métricas por janela

- precision, recall e F1;
- PR-AUC, preferida em cenário desbalanceado;
- ROC-AUC apenas como métrica complementar;
- matriz de confusão;
- distribuição do score saudável × falha.

### Métricas por evento e operação

- percentual de eventos detectados;
- antecedência até o evento;
- atraso de detecção;
- falsos alarmes por dia/semana;
- duração de alarmes espúrios;
- estabilidade do índice de saúde;
- latência p50/p95 da inferência.

### Experimentos mínimos

1. baseline estatístico;
2. Isolation Forest;
3. LSTM Autoencoder;
4. duas dimensões de janela;
5. dois limiares de alarme;
6. com e sem atributos derivados;
7. ablação de variáveis;
8. teste de dados ausentes e gap temporal;
9. teste de mudança de regime;
10. análise de sensibilidade do limiar.

Salvar configuração, seed, versão do dataset, commit, métricas e artefatos de cada execução.

---

## 11. Explicabilidade e índice de saúde

O painel deve mostrar por que o sistema sinalizou uma condição.

- erro de reconstrução total;
- contribuição do erro por variável;
- tendência recente contra distribuição saudável;
- limiar usado e versão do modelo;
- qualidade dos dados da janela;
- explicação do baseline clássico para comparação.

Índice de saúde sugerido:

```text
health_index = 100 × clamp(1 - normalized_anomaly_score, 0, 1)
```

A normalização deve ser calibrada na validação e documentada. Estados de interface:

- `normal`;
- `attention`;
- `alert`;
- `insufficient_data`;
- `model_unavailable`.

Nunca esconder `insufficient_data` como condição normal.

---

## 12. Modelo de dados no Railway

Tabelas mínimas:

### `datasets`

`id`, `name`, `source_url`, `license`, `version`, `sha256`, `time_start`, `time_end`, `metadata`, `created_at`.

### `ingestion_runs`

`id`, `dataset_id`, `status`, `row_count`, `quality_report`, `pipeline_version`, `started_at`, `finished_at`, `error_message`.

### `signal_samples`

`id`, `dataset_id`, `timestamp`, valores de sinal definidos após a auditoria, `quality_flags`.

Criar índice composto por `(dataset_id, timestamp)`. Se o volume não justificar persistir cada amostra, armazenar apenas série processada necessária à demo e documentar a decisão.

### `model_versions`

`id`, `name`, `algorithm`, `artifact_path`, `dataset_version`, `feature_schema`, `hyperparameters`, `metrics`, `status`, `git_commit`, `created_at`.

### `prediction_runs`

`id`, `model_version_id`, `window_start`, `window_end`, `anomaly_score`, `health_index`, `state`, `feature_contributions`, `latency_ms`, `created_at`.

### `alerts`

`id`, `prediction_run_id`, `severity`, `reason`, `acknowledged`, `acknowledged_at`, `notes`.

### `evaluation_runs`

`id`, `model_version_id`, `configuration`, `metrics`, `confusion_matrix`, `started_at`, `finished_at`.

Usar JSONB para configurações e resultados flexíveis, mas manter campos usados em filtros como colunas tipadas.

Variáveis:

```dotenv
DATABASE_URL=postgresql+psycopg://USER:PASSWORD@HOST:PORT/DB?sslmode=require
MODEL_ARTIFACT_DIR=artifacts
APP_ENV=development
CORS_ORIGINS=http://localhost:5173
```

Nunca enviar `DATABASE_URL` ao frontend ou versionar `.env`.

---

## 13. API mínima

### Saúde e catálogo

- `GET /api/health`
- `GET /api/datasets`
- `GET /api/datasets/{id}/quality`

### Sinais

- `GET /api/signals/range?start=&end=&downsample=`
- `GET /api/signals/summary`

### Modelos

- `GET /api/models`
- `GET /api/models/{id}`
- `POST /api/models/{id}/activate`
- `POST /api/inference/range`

### Monitoramento

- `GET /api/monitoring/current`
- `GET /api/monitoring/timeline`
- `GET /api/alerts`
- `PATCH /api/alerts/{id}`

### Avaliação

- `GET /api/evaluations`
- `GET /api/evaluations/{id}`
- `POST /api/evaluations/run`

Treino deve ser executado por script, não por endpoint público, no MVP:

```powershell
.\.venv\Scripts\python.exe -m backend.app.training.train --config configs\lstm_autoencoder.yaml
```

---

## 14. Interface React — “Hydro Condition Intelligence”

Direção visual:

- estética de sala de controle contemporânea;
- fundo azul-marinho quase preto;
- ciano para fluxo e dados;
- verde, âmbar e vermelho apenas para estado operacional;
- tipografia limpa, números tabulares e bastante espaço negativo;
- animações discretas que reforcem fluxo, atualização e transição de estado;
- respeitar `prefers-reduced-motion`.

### Página 1 — Visão geral

- índice de saúde em destaque;
- estado atual e confiança;
- última janela processada;
- tendência de vibração;
- score de anomalia e limiar;
- alertas recentes;
- qualidade dos dados;
- versão do modelo ativo.

### Página 2 — Explorador de sinais

- gráfico temporal com zoom;
- seleção de variáveis;
- regiões de treino, validação e teste;
- marcação de falha e alarmes;
- visualização do dado bruto e processado;
- gaps e imputações visíveis.

### Página 3 — Laboratório de modelos

- tabela comparativa de baseline, Isolation Forest e LSTM;
- PR-AUC, recall de eventos, falsos alarmes e antecedência;
- curvas precision-recall;
- matriz de confusão;
- distribuição de scores;
- justificativa do modelo campeão.

### Página 4 — Explicabilidade

- contribuição por variável;
- erro de reconstrução ao longo da janela;
- comparação com envelope saudável;
- dados, modelo e limiar usados;
- aviso explícito sobre limites da explicação.

### Página 5 — Linhagem e Model Card

- origem e licença do dataset;
- versões do pipeline e do modelo;
- período de treino;
- limitações, riscos e usos não recomendados;
- histórico de experimentos;
- links para código e documentação.

Responsividade:

- desktop é o modo principal de demonstração;
- tablets devem manter gráficos utilizáveis;
- mobile deve permitir consulta, sem tentar reproduzir uma sala de controle inteira.

---

## 15. Marcos de implementação

### Marco 0 — Auditoria e repositório

- verificar ambiente;
- criar estrutura, `.gitignore`, `.env.example` e documentação;
- confirmar criação do venv e instalação npm local.

**Aceite:** backend e frontend exibem versões e iniciam sem privilégio administrativo.

### Marco 1 — Dataset e qualidade

- baixar de forma documentada;
- validar licença e hashes;
- criar dicionário e relatório de qualidade;
- definir formalmente a tarefa de ML.

**Aceite:** qualquer pessoa consegue reproduzir a preparação do dado bruto.

### Marco 2 — Pipeline temporal

- implementar limpeza, split temporal, transformação e janelas;
- adicionar testes de vazamento e fronteiras.

**Aceite:** treino, validação e teste são reproduzíveis e isolados.

### Marco 3 — Baselines

- estatístico e Isolation Forest;
- métricas por janela e evento;
- primeiro relatório.

**Aceite:** existe uma referência quantitativa antes da rede neural.

### Marco 4 — LSTM Autoencoder

- treino CPU;
- early stopping;
- persistência do scaler, configuração e pesos;
- escolha de limiar na validação.

**Aceite:** inferência reproduz o resultado do experimento em processo separado.

### Marco 5 — Comparação e explicabilidade

- protocolo final de avaliação;
- contribuição por variável;
- seleção transparente do campeão.

**Aceite:** relatório mostra benefícios e limitações de cada método.

### Marco 6 — Railway PostgreSQL e API

- criar banco exclusivo;
- configurar migrações;
- persistir catálogo, modelos e previsões;
- implementar endpoints.

**Aceite:** API retorna monitoramento e avaliação sem expor credenciais.

### Marco 7 — Interface React

- visão geral, sinais, laboratório e Model Card;
- loading, vazio, erro e dados insuficientes;
- acessibilidade e responsividade.

**Aceite:** a demonstração completa não exige notebook ou Swagger.

### Marco 8 — Robustez

- testes backend/frontend;
- dados ausentes, modelo indisponível e banco indisponível;
- lint, tipos e CI no GitHub Actions.

**Aceite:** CI executa testes e build em cada push.

### Marco 9 — Publicação e narrativa

- screenshots/GIF curto;
- arquitetura e resultados no README;
- deploy opcional;
- roteiro de demonstração.

**Aceite:** recrutador entende problema, método, resultado e limite em cinco minutos.

---

## 16. Testes obrigatórios

Backend:

- schema e ordem temporal;
- detecção de duplicidades e gaps;
- scaler ajustado somente no treino;
- janelas não atravessam splits;
- inferência determinística com seed/modelo fixos;
- limiar correto por versão;
- cálculo do índice de saúde;
- serialização e carregamento de artefatos;
- contratos da API;
- falha segura quando o modelo ou banco não estão disponíveis.

Frontend:

- estados de carregamento, sucesso, vazio e erro;
- renderização de alertas e qualidade de dados;
- filtros temporais;
- navegação por teclado;
- gráficos com descrição textual ou tabela alternativa;
- nenhum segredo no bundle.

---

## 17. Segurança, ética e comunicação

- não incluir dados internos ou confidenciais;
- não usar marca CTG como se o projeto fosse produto oficial;
- atribuir corretamente dataset e autores;
- deixar claro que os limiares são experimentais;
- não afirmar causalidade com base apenas em correlação;
- não ocultar falsos negativos;
- não permitir upload arbitrário no MVP público;
- limitar tamanho e período das consultas;
- parametrizar SQL;
- ocultar stack traces na interface;
- registrar apenas dados necessários.

---

## 18. README final

O README deve conter, nesta ordem:

1. problema operacional;
2. resultado principal em uma frase;
3. screenshot ou GIF;
4. arquitetura;
5. dataset, licença e limitações;
6. formulação do problema;
7. protocolo temporal e prevenção de leakage;
8. modelos comparados;
9. métricas e resultados;
10. explicabilidade;
11. execução local sem Docker;
12. variáveis de ambiente;
13. testes;
14. estrutura do repositório;
15. usos não recomendados;
16. próximos passos.

Evitar começar o README com uma lista de bibliotecas.

---

## 19. Roteiro de demonstração na entrevista

1. Apresentar o ativo, o sinal e o evento de falha.
2. Mostrar a linha do tempo e a separação temporal.
3. Comparar baseline e rede neural.
4. Exibir o primeiro alerta e sua antecedência.
5. Mostrar falsos alarmes, não apenas acertos.
6. Abrir a explicabilidade de uma janela.
7. Mostrar Model Card, dataset e versão do pipeline.
8. Concluir com como o método seria validado com especialistas antes de uso real.

Resposta curta esperada para “por que uma rede neural?”:

> A rede foi tratada como hipótese, não como premissa. Comparei seu ganho em padrões temporais não lineares contra métodos mais simples, usando split temporal, falsos alarmes e antecedência como critérios operacionais.

---

## 20. Escopo MVP e extensões

### MVP obrigatório para a entrevista

- dataset real e documentado;
- pipeline temporal reproduzível;
- baseline estatístico;
- Isolation Forest;
- LSTM Autoencoder;
- comparação com métricas operacionais;
- FastAPI;
- quatro telas React principais;
- Railway PostgreSQL;
- testes essenciais;
- README com resultados e limitações.

### Extensões, somente após o MVP

- 1D-CNN Autoencoder;
- estimação de RUL se os dados permitirem;
- SHAP para modelo clássico;
- detecção de drift;
- simulação de streaming;
- fila de alertas;
- autenticação;
- publicação integral em nuvem.

---

## 21. Definição de pronto

O projeto estará pronto quando:

- funcionar em Windows sem admin e sem Docker;
- puder ser reproduzido a partir do dataset original;
- não tiver vazamento temporal;
- comparar pelo menos três abordagens;
- justificar o modelo escolhido com métricas operacionais;
- disponibilizar inferência por API;
- persistir versões e previsões no Railway;
- apresentar índice de saúde, alarmes, sinais e avaliação em React;
- possuir testes e CI;
- documentar limitações e usos inadequados;
- permitir uma demonstração convincente em até cinco minutos.

---

## 22. Primeira etapa ao iniciar a implementação

Executar somente o **Marco 0** e, em seguida, o **Marco 1**. Não desenvolver a rede neural antes de produzir o relatório de qualidade e definir formalmente o problema que o dataset permite resolver.

Primeiro resultado esperado:

```text
docs/dicionario-de-dados.md
docs/relatorio-qualidade-dataset.md
docs/formulacao-do-problema.md
data/README.md
```

