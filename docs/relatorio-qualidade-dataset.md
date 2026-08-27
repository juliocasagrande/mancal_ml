# Relatório de qualidade do dataset

Gerado manualmente a partir da auditoria de `data/raw/` na etapa do
Marco 1. Reprodução:

```powershell
.\.venv\Scripts\python.exe backend\scripts\download_dataset.py
.\.venv\Scripts\python.exe backend\scripts\audit_dataset.py
```

## Identificação

- **dataset_version:** `2022-10-06-v1` (data de publicação no Figshare + versão v1 do DOI)
- **Data do download:** 2026-08-26
- **Hash dos arquivos:** ver `data/dataset_manifest.json` (SHA-256 por arquivo)
- **Código responsável pela auditoria:** `backend/scripts/audit_dataset.py` (commit a registrar no primeiro commit deste repositório)

## Escopo considerado

Este relatório cobre os 6 arquivos da unidade **G1** usados no MVP
(`June.csv` a `Nov.csv`). Os 2 arquivos da unidade G4 foram inspecionados
mas excluídos do escopo (ver `dicionario-de-dados.md` e
`formulacao-do-problema.md`) e não são detalhados linha a linha aqui.

## Intervalo temporal e volume

| Arquivo | Início | Fim | Linhas | Duplicados de timestamp | Ordenado no arquivo |
|---|---|---|---:|---:|---|
| June.csv | 2020-06-01 00:00 | 2020-06-28 18:30 | 4000 | 0 | sim |
| July.csv | 2020-07-01 00:00 | 2020-07-28 18:30 | 4000 | 0 | sim |
| Aug.csv | 2020-08-01 00:00 | 2020-08-28 18:30 | 4000 | 0 | sim |
| SEP.csv | 2020-09-01 00:10 | 2020-09-28 18:30 | 4000 | 0 | não (1 timestamp não parseável) |
| Oct.csv | 2020-10-01 00:10 | 2020-10-28 18:30 | 4000 | 0 | não (1 timestamp não parseável) |
| Nov.csv | 2020-11-01 00:10 | 2020-11-28 18:30 | 4000 | 0 | não (1 timestamp não parseável) |

**Achado crítico:** cada arquivo cobre apenas do dia 1 ao dia 28 do mês
(4000 linhas × 10 min ≈ 27,8 dias), nunca o mês completo. Os últimos 1 a 3
dias de cada mês (29–31, quando existentes) **não estão presentes** em
nenhum arquivo. Isso não é um gap dentro do arquivo — é uma fronteira dura
de cobertura que deve ser respeitada no split temporal (Marco 2): não
assumir continuidade entre o fim de um arquivo e o início do próximo mês.

Não há sobreposição nem gap interno maior que o passo nominal dentro de
cada arquivo individual — a frequência observada é 10 minutos constante
(mín = mediana = máx do delta entre timestamps consecutivos).

## Valores ausentes e anômalos por arquivo

| Arquivo | NA em colunas numéricas | Zeros em `generator_power` | Zeros nos canais de vibração | Observação |
|---|---:|---:|---:|---|
| June.csv | 1 linha (última) | 29 (0,7%) | 27 (0,7%) | Padrão normal de operação |
| July.csv | 0 | 32 (0,8%) | 30 (0,8%) | Padrão normal de operação |
| Aug.csv | 1 linha (última) | 4 (0,1%) | 0 | Padrão normal de operação |
| SEP.csv | 1 linha (última) | 1419 (**35,5%**) | 1416 (**35,4%**) | Unidade parece parada/parcialmente offline em boa parte do mês |
| Oct.csv | 1 linha (última) | 3081 (**77,0%**) | 3965 (**99,1%**) | Unidade majoritariamente offline — potencial evento operacional relevante |
| Nov.csv | 1 linha (última) | 6 (0,1%) | 0 | Padrão normal de operação |

A "1 linha ausente" repetida em vários arquivos corresponde à última linha
de cada CSV, onde os campos numéricos ficaram vazios (mas o timestamp
existe) — padrão consistente com truncamento no fim da exportação SCADA.

**Canal morto:** `temp_lower_guide_pad1` (`RIO1 lower guide pad 1#
temperature`) é **100% zero em Aug, SEP, Oct e Nov**, mas tem valores
plausíveis em June e July. Interpretação mais provável: sensor ou canal de
aquisição inoperante a partir de agosto/2020. Este canal não deve ser
usado como está; decisão de tratamento (excluir vs. imputar vs. usar
apenas em June/July) fica para o Marco 2, documentada como decisão
explícita.

**Períodos de baixa/zero atividade (SEP e, principalmente, Oct):** a
combinação de potência ≈ 0, velocidade baixa e vibração ≈ 0 em grandes
blocos de SEP.csv e Oct.csv é consistente com a unidade fora de operação
(parada programada, manutenção ou falha), não com ruído de sensor pontual.
**Isto não deve ser interpretado automaticamente como "evento de falha do
mancal"** — pode ser parada operacional normal. Não há metadado que
confirme a causa. Tratado como hipótese a validar, não como rótulo.

## Duplicidade e ordenação

Nenhum arquivo tem timestamps duplicados. SEP, Oct e Nov têm exatamente 1
timestamp que falhou no parse (`errors="coerce"` → `NaT`), o que quebra a
checagem de monotonicidade nesses três arquivos — a ordenação das linhas
originais parece correta; o problema é um valor de data malformado em uma
única linha por arquivo, a ser tratado na ingestão (Marco 2).

## Frequência

- Frequência nominal: 10 minutos (144 amostras/dia).
- Frequência observada: constante em 10 minutos dentro de cada arquivo,
  sem gaps internos além da linha final malformada.
- **Sem resampling necessário dentro de cada mês.** O resampling, se
  usado, servirá apenas para features agregadas (Seção 8.3 do blueprint),
  não para corrigir a frequência bruta.

## Regras já aplicadas neste relatório

1. Leitura com `pandas.read_csv`, sem alteração dos arquivos em `data/raw/`.
2. Parse de timestamp com formato `%Y/%m/%d %H:%M:%S`, erros coagidos a `NaT`.
3. Remoção da 14ª coluna vazia (`Unnamed`) antes da contagem de valores.
4. Nenhuma imputação, remoção de linha ou resampling foi aplicada — este
   relatório descreve o dado bruto, não um dado tratado.

## Decisões pendentes para o Marco 2

- Definir tratamento de `temp_lower_guide_pad1` (canal morto em 4/6 meses).
- Definir tratamento da linha final malformada de cada arquivo.
- Definir se SEP.csv e Oct.csv entram no treino (trecho saudável) ou são
  isolados como período suspeito/de teste, dado o padrão de baixa
  atividade.
- Confirmar limites de fronteira entre arquivos mensais no split temporal
  (nenhuma janela pode atravessar a lacuna entre o dia 28 de um mês e o
  dia 1 do mês seguinte, pois os dias 29–31 não existem no dataset).
