# Hydro Condition Intelligence — frontend

Interface React do sistema de manutenção preditiva do mancal-guia (Marco 7
do blueprint em `PROJETO_01_MANUTENCAO_PREDITIVA_UHE.md`). Consome a API
FastAPI de `backend/` — nunca acessa o Postgres diretamente.

## Setup local

```powershell
cd frontend
npm install
copy .env.example .env.local
npm run dev
```

`VITE_API_BASE_URL` (em `.env.local`) aponta para a API local por padrão
(`http://localhost:8000`). Suba a API antes (`backend/README` ou
`uvicorn app.main:app --reload` a partir de `backend/`, com
`PYTHONPATH=backend`).

## Páginas

1. Visão geral — `/`
2. Explorador de sinais — `/sinais`
3. Laboratório de modelos — `/laboratorio`
4. Explicabilidade — `/explicabilidade`
5. Linhagem e Model Card — `/linhagem`

## Scripts

- `npm run dev` — servidor de desenvolvimento
- `npm run build` — `tsc -b && vite build`
- `npm run lint` — oxlint
- `npm run test` — Vitest + React Testing Library
- `npm run preview` — serve o build de produção localmente

## Notas de arquitetura

- Dados vêm exclusivamente da API (`src/api/`), via TanStack Query
  (`src/api/hooks.ts`). Nenhuma chamada direta ao banco.
- `src/components/StateBoundary.tsx` centraliza loading/erro/vazio e os
  estados de domínio (`insufficient_data`, `model_unavailable`) — toda
  página os usa em vez de tratar isso solto.
- Todo gráfico Recharts fica dentro de
  `src/components/ChartWithFallback.tsx`, que oferece uma tabela
  equivalente para acessibilidade.
- Tema fixo (sala de controle, fundo navy) em `src/styles/theme.css`.
  Animações respeitam `prefers-reduced-motion`.
