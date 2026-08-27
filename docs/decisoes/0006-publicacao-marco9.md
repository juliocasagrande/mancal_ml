# ADR 0006 — Publicação e narrativa (Marco 9)

## Contexto

Seção 15 do blueprint pede, no Marco 9: screenshots/GIF, arquitetura e
resultados no README final, deploy opcional e roteiro de demonstração.
O deploy foi incluído a pedido explícito (o projeto já tinha Postgres no
Railway desde o Marco 6 — ver `docs/decisoes/0004-railway-postgres-e-api.md`
— faltava publicar a API e o frontend).

## Decisões

- **Backend publicado no Railway** como um segundo serviço (`backend`) no
  mesmo projeto `hydro-bearing-pm`, a partir do repositório GitHub
  (`juliocasagrande/mancal_ml`, branch `master`), `rootDirectory=backend`.
  Build: `pip install -r requirements.txt` com
  `PIP_EXTRA_INDEX_URL=https://download.pytorch.org/whl/cpu` (variável de
  ambiente do serviço) — sem essa variável o `torch==2.13.0+cpu` não é
  resolvido, porque esse identificador de build só existe no índice da
  PyTorch, não no PyPI padrão (mesma necessidade do CI, ver `ci.yml`).
  Start: `alembic upgrade head && uvicorn app.main:app --host 0.0.0.0
  --port $PORT`. `DATABASE_URL` referencia
  `${{postgres.DATABASE_URL}}` (variável de referência entre serviços do
  mesmo projeto Railway, resolvida automaticamente).
- **`torch`/`pandas`/`scipy`/`scikit-learn` continuam no build da API**
  mesmo não sendo importados por `app.main:app` (só os módulos de treino
  e inferência local os usam) — manter um único `requirements.txt` para
  todo o backend evita duas listas de dependência divergindo com o tempo;
  o custo é um build mais lento na nuvem, aceitável para este projeto.
- **Nenhum artefato de modelo (`artifacts/`) foi publicado no Railway.**
  Os endpoints de leitura (`/api/monitoring/*`, `/api/models`,
  `/api/evaluations`) só consultam o Postgres, já populado pelo
  `populate_db.py` local (Marco 6) — não carregam pesos do LSTM em
  tempo de execução. Treino e inferência em lote continuam scripts
  locais (Seção 13 do blueprint: "Treino deve ser executado por script,
  não por endpoint público").
- **Frontend publicado no Vercel** (detecção automática de projeto
  Vite), com `frontend/.env.production` fixando
  `VITE_API_BASE_URL` para o domínio público do backend no Railway —
  Vite embute variáveis `VITE_*` em tempo de build, então isso precisa
  estar resolvido antes do `vite build` do Vercel, não pode ser uma
  variável de runtime.
- **`CORS_ORIGINS`** do backend inclui o domínio publicado do Vercel além
  de `localhost:5173`, para a demonstração pública funcionar sem abrir
  CORS para qualquer origem.
- **Bug corrigido durante este marco**: o badge de estado no cabeçalho
  (`AppShell.tsx`) estava fixo em `state="normal"`, independente do
  estado real (`useMonitoringCurrent`) mostrado no restante da página —
  um recrutador veria "Normal" no topo e "Alerta" no índice de saúde ao
  mesmo tempo. Corrigido para usar o mesmo estado da Página 1. Não é
  regressão de Marco 8 (o teste de acessibilidade do `AppShell` não
  cobria o conteúdo do badge, só a navegação por teclado) — ficou sem
  cobertura desde o Marco 7. Testes, lint e build do frontend
  re-executados após a correção.

## Consequência

- Qualquer redeploy do backend no Railway reconstrói `torch` do zero
  (sem cache de camada entre builds distintos neste plano) — o build
  leva ~3 minutos. Aceitável para a cadência de um projeto de portfólio.
- Se o domínio do Vercel mudar (ex.: renomear o projeto), `CORS_ORIGINS`
  no Railway e `frontend/.env.production` precisam ser atualizados
  manualmente — não há automação entre os dois serviços.
- Reproduzir a publicação exige acesso ao projeto Railway
  `hydro-bearing-pm` e a uma conta Vercel própria; instruções de
  reprodução local (sem depender de nenhum dos dois) permanecem
  documentadas no `README.md`.
