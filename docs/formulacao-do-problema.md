# Formulação do problema

Este documento fixa, antes de qualquer modelagem, qual tarefa de ML o
dataset efetivamente permite resolver — conforme exigido pela Seção 3 do
blueprint do projeto. Baseado em `docs/dicionario-de-dados.md` e
`docs/relatorio-qualidade-dataset.md`.

## O que o dataset NÃO permite afirmar

- **Não há 12 meses de uma única unidade.** Há 6 meses (jun–nov/2020) da
  unidade G1 e 2 arquivos fragmentados e não contínuos da unidade G4
  (out/2021–mai/2022), com esquema de colunas diferente. As duas unidades
  não podem ser tratadas como uma série única.
- **Não há rótulo de falha.** Nenhum arquivo contém uma coluna categórica
  de estado (saudável/falha) ou um identificador de evento. Qualquer
  "falha" mencionada na descrição pública do dataset não está marcada nos
  dados.
- **Não há confirmação de causa** para os períodos de baixa atividade
  observados em `SEP.csv` e `Oct.csv` (potência e vibração próximas de
  zero). Pode ser parada programada, redução de carga sazonal (o próprio
  Figshare menciona período de águas baixas) ou uma falha — os dados não
  distinguem essas hipóteses.
- Consequentemente, **não se pode formular prognóstico/RUL nem
  classificação temporal saudável × falha com rótulo confiável** neste
  momento. Afirmar antecedência de detecção "em dias" antes de uma falha
  rotulada seria uma afirmação não sustentada pelos dados.

## Escopo de dados do MVP

- **Unidade:** G1 (mancal-guia, sinal `vib_tgb_x`, mais os demais canais
  de vibração e temperatura de G1 como contexto).
- **Período:** junho a novembro de 2020, um arquivo por mês, cada um
  cobrindo do dia 1 ao dia 28.
- **Unidade G4 excluída do MVP** — candidata a extensão futura, exigiria
  harmonização de esquema e não tem continuidade temporal com G1.

## Tarefa formal escolhida

**Detecção não supervisionada de anomalias / degradação de condição**,
opção 1 da Seção 3 do blueprint — a única sustentada pelos dados
disponíveis.

- O modelo é treinado apenas com o que for identificado como período de
  operação normal dentro do trecho mais antigo (June/July, os dois meses
  com o canal de temperatura completo e sem grandes blocos de
  inatividade).
- A saída é um **score de anomalia contínuo** (erro de reconstrução /
  distância a um envelope saudável), não uma classificação binária
  saudável/falha.
- Os blocos de baixa atividade de SEP e Oct são tratados como **períodos
  suspeitos de teste**, não como "eventos de falha confirmados". O
  relatório de avaliação deve nomeá-los como "período de operação
  anômala/atípica", nunca como "falha do mancal", a menos que uma fonte
  externa confirme a causa.
- Sem rótulo, as métricas de "recall de eventos" e "antecedência de
  detecção" da Seção 10 do blueprint serão calculadas usando os blocos de
  baixa atividade como **proxy fraco** de evento anômalo, com essa
  limitação declarada explicitamente em todo relatório e no Model Card
  (Página 5 do frontend). Isto é uma hipótese de avaliação, não uma
  verdade de campo.

## Consequência para os marcos seguintes

- Marco 2 (pipeline temporal): treino = June+July; validação = August;
  teste = SEP+Oct+Nov (contém os blocos suspeitos). Fronteiras de mês são
  fronteiras rígidas de split — nenhuma janela atravessa a lacuna entre
  dia 28 e o início do mês seguinte.
- Marco 3–5 (modelagem e avaliação): todo experimento reporta explicitamente
  que os "eventos" avaliados são proxies não confirmados, e a matriz de
  decisão do modelo campeão (Seção 9.4 do blueprint) deve favorecer baixa
  taxa de falso alarme, já que não há confirmação de verdade de campo para
  validar recall.
- README e Model Card devem repetir esta limitação de forma explícita —
  não apresentar o sistema como detector de falha de mancal validado, e
  sim como detector de desvio de condição operacional em relação ao
  padrão saudável observado.
