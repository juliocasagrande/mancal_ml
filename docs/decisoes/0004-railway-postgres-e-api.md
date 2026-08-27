# ADR 0004 — Provisionamento do Postgres no Railway e API (Marco 6)

## Contexto

Seção 12 do blueprint pede um PostgreSQL dedicado no Railway. O MCP do
Railway disponível não expõe um botão "Add PostgreSQL Plugin" (que gera
credenciais e `DATABASE_URL` automaticamente) — apenas `create-service`
a partir de uma imagem Docker.

## Decisões

- **Projeto**: `hydro-bearing-pm` (nome curto — o nome completo do
  blueprint foi rejeitado pela validação do Railway).
- **Serviço**: imagem `postgres` oficial, com `POSTGRES_USER`,
  `POSTGRES_PASSWORD` (gerado aleatoriamente, 24 bytes) e `POSTGRES_DB`
  definidos manualmente como variáveis do serviço — o equivalente ao que
  o plugin oficial faria automaticamente.
- **`PGDATA`** apontado para um subdiretório do volume
  (`/var/lib/postgresql/data/pgdata`), não a raiz do volume — evita o
  aviso/erro do Postgres sobre o diretório de dados não estar vazio por
  causa de `lost+found`.
- **Volume persistente** (`postgres-data`) montado em
  `/var/lib/postgresql/data`, para não perder dados a cada redeploy.
- **`DATABASE_URL`** definida como variável do próprio serviço Postgres,
  usando `${{RAILWAY_PRIVATE_DOMAIN}}` — funciona para qualquer outro
  serviço Railway no mesmo projeto (o backend, quando publicado), mas
  **não é acessível da máquina local**.
- **TCP proxy** criado (`create-tcp-proxy`, porta 5432) para permitir
  desenvolvimento e migração a partir da máquina local — gera um host
  público (`switchyard.proxy.rlwy.net:<porta>`). A `DATABASE_URL` local
  (em `.env`, nunca versionado) usa esse endpoint público.
- **UUID portátil**: os modelos usam `sqlalchemy.Uuid()` (introduzido no
  SQLAlchemy 2.0), não o tipo `postgresql.UUID` específico do dialeto.
  Isso permite rodar os testes da API contra SQLite em memória
  (`backend/tests/test_api.py`), sem depender do Postgres do Railway
  para cada execução de teste — mais rápido e sem custo de rede. No
  Postgres, `Uuid()` compila para o mesmo tipo nativo `uuid`.

## Consequência

- Qualquer pessoa reproduzindo o projeto precisa criar seu próprio
  serviço Postgres (Railway ou outro) e apontar `DATABASE_URL` no seu
  `.env` — as credenciais geradas aqui são específicas desta instância e
  nunca foram commitadas.
- `backend/scripts/populate_db.py` assume que os scripts de pipeline
  (`build_dataset.py`, `run_baselines.py`, `train_lstm.py`,
  `run_decision_matrix.py`) já rodaram e que `alembic upgrade head` já
  foi aplicado.
