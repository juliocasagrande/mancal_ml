# Dados

Este diretório nunca recebe dados brutos versionados no Git (ver `.gitignore`).
Os arquivos originais são obtidos por script documentado e tratados como
somente leitura.

## Estrutura

- `raw/` — arquivos exatamente como baixados da fonte original. Nunca editar.
- `interim/` — dados limpos, normalizados e com resampling, ainda não
  organizados em janelas temporais.
- `processed/` — janelas temporais e atributos derivados, prontos para
  treino/avaliação, com metadados de split (treino/validação/teste).

## Fonte

**Bearing Vibration Dataset of a Hydropower Project**

- Autor: Yasir Saleem Afridi
- DOI: [10.6084/m9.figshare.21290895.v1](https://doi.org/10.6084/m9.figshare.21290895.v1)
- URL: <https://figshare.com/articles/dataset/Bearing_Vibration_Dataset_of_a_Hydropower_Project/21290895>
- Data de publicação: 2022-10-06
- Licença: CC BY 4.0
- Conteúdo: doze meses de dados de vibração horizontal do mancal-guia da
  turbina da Unidade 01, obtidos do SCADA de uma usina hidrelétrica de
  969 MW (quatro unidades de 242,25 MW) operando no Paquistão. Inclui
  períodos saudáveis e de falha, cobrindo variação sazonal (período de
  águas baixas, com maior turbulência, e período de pico).

## Como baixar

```powershell
.\.venv\Scripts\python.exe backend\scripts\download_dataset.py
```

O script (`backend/scripts/download_dataset.py`):

1. baixa cada arquivo listado no manifesto (`data/dataset_manifest.json`);
2. calcula e confere o hash SHA-256 de cada arquivo baixado;
3. grava os arquivos em `data/raw/` (pula o download se o arquivo já
   existir e o hash já conferir);
4. falha e remove o arquivo se o hash não bater com o manifesto.

## Achados da auditoria (Marco 1 — confirmado)

Ver detalhes completos em `docs/dicionario-de-dados.md` e
`docs/relatorio-qualidade-dataset.md`.

- O dataset **não é** uma série contínua de 12 meses de uma única
  unidade. São 6 meses (jun–nov/2020) da unidade **G1**, mais 2 arquivos
  fragmentados e descontínuos da unidade **G4** (out/2021–mai/2022), com
  esquema de colunas diferente. O MVP usa somente os 6 arquivos de G1.
- Cada arquivo mensal cobre apenas do dia 1 ao dia 28 do mês (nunca o mês
  completo) — fronteira rígida a respeitar no split temporal.
- O ID de Figshare `37771965` é um duplicado byte-a-byte de `Aug.csv`
  (mesmo SHA-256); não é um mês adicional.
- **Não há coluna de rótulo de falha em nenhum arquivo.** A tarefa de ML
  foi formalizada como detecção não supervisionada de anomalias — ver
  `docs/formulacao-do-problema.md`.
- O canal `temp_lower_guide_pad1` está com 100% de zeros em 4 dos 6
  meses de G1 (possível sensor inoperante).
- `SEP.csv` e, principalmente, `Oct.csv` têm grandes blocos de
  potência/vibração próximas de zero, consistentes com a unidade fora de
  operação — causa não confirmada pelos dados (pode ser parada
  programada, não necessariamente falha do mancal).
