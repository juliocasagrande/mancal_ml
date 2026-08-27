# ADR 0002 — Split temporal e janelamento (Marco 2)

## Contexto

`docs/formulacao-do-problema.md` definiu a tarefa como detecção não
supervisionada de anomalias sobre a unidade G1, com 6 arquivos mensais
(jun–nov/2020), cada um cobrindo apenas do dia 1 ao 28. Não há dados dos
dias 29–31 em nenhum arquivo — uma lacuna real, não um gap de sensor.

## Decisão

- **Split por arquivo inteiro**, nunca dentro de um arquivo:
  - treino: `June.csv`, `July.csv`;
  - validação: `Aug.csv`;
  - teste: `SEP.csv`, `Oct.csv`, `Nov.csv`.
- **Janelamento nunca cruza arquivo.** `make_windows` agrupa por
  `source_file` antes de gerar janelas deslizantes, então uma janela
  jamais mistura dois meses — o que também garante, por construção, que
  nenhuma janela cruza uma fronteira de split (já que cada arquivo
  pertence a um único split).
- **Tamanho de janela inicial: 36 amostras (6 horas), passo de 6 amostras
  (1 hora).** Escolha de partida documentada aqui, não definitiva — a
  Seção 10 do blueprint pede comparação de pelo menos duas dimensões de
  janela como experimento (Marco 3+).
- **Scaler ajustado exclusivamente com janelas de treino** (`fit_scaler`
  só aceita a matriz já filtrada).
- Canal `temp_lower_guide_pad1` (morto em 4/6 meses) excluído das colunas
  de modelagem (`MODELING_COLUMNS`), mas mantido no CSV limpo intermediário
  para não perder informação de June/July.

## Consequência

- Testes (`backend/tests/test_windows_no_leakage.py`) verificam
  adversarialmente que nenhuma janela mistura arquivos mesmo com
  timestamps sobrepostos entre arquivos sintéticos, e que o scaler nunca
  reflete dados fora do treino.
- Janelas de `Oct.csv` (grande bloco de valores ~zero) terão
  estatísticas de assimetria/curtose com `NaN` ou instabilidade numérica
  (variância ~0) — tratamento de outliers/NaN em atributos fica para o
  Marco 3, ao lado dos modelos que consumem essas features.
