# Roteiro de demonstração (Marco 9)

Roteiro de ~5 minutos para apresentar o projeto a um recrutador ou
avaliador técnico, seguindo a Seção 19 do blueprint. Usa a interface
React (`frontend/`) contra a API publicada no Railway ou uma instância
local.

## Antes de começar

- Confirmar que `GET /api/health` responde e que `/api/monitoring/current`
  não retorna `model_unavailable` nem `insufficient_data`.
- Abrir a Página 1 (Visão geral) já carregada, para não perder tempo com
  o primeiro carregamento durante a apresentação.

## Passo a passo

1. **Apresentar o ativo, o sinal e o evento** — Página 1 (Visão geral).
   Mostrar o índice de saúde, o estado atual e explicar em uma frase o
   ativo: mancal-guia da turbina da Unidade 01 de uma UHE de 969 MW,
   dataset público de vibração (`data/README.md`).
2. **Mostrar a linha do tempo e a separação temporal** — Página 2
   (Explorador de sinais). Apontar as regiões de treino, validação e
   teste e o bloco de baixa atividade de outubro (o proxy de anomalia
   usado — ver `docs/formulacao-do-problema.md`).
3. **Comparar baseline e rede neural** — Página 3 (Laboratório de
   modelos). Tabela comparativa (`baseline_zscore`, `isolation_forest`,
   `lstm_autoencoder`), PR-AUC e curva precision-recall. Destacar que o
   campeão (`lstm_autoencoder`) venceu por margem estreita
   (`docs/protocolo-de-avaliacao.md`).
4. **Exibir o primeiro alerta e sua antecedência** — voltar à Página 1 ou
   à lista de alertas: mostrar o alerta gerado no bloco de outubro e sua
   janela de detecção.
5. **Mostrar falsos alarmes, não apenas acertos** — Página 3: falsos
   alarmes por dia de cada modelo (`docs/resultados.md`). Deixar claro
   que nenhum modelo é livre de falso alarme.
6. **Abrir a explicabilidade de uma janela** — Página 4
   (Explicabilidade): contribuição por variável do erro de reconstrução,
   comparação com o envelope saudável, aviso sobre limites da explicação.
7. **Mostrar Model Card, dataset e versão do pipeline** — Página 5
   (Linhagem): origem/licença do dataset, versão do modelo, limitações e
   usos não recomendados.
8. **Concluir com a validação necessária antes de uso real** — o sistema
   é apoio à decisão; qualquer promoção a alarme operacional exigiria
   rótulos confirmados por um especialista de manutenção, mais eventos
   de falha reais no histórico e revisão do limiar com a equipe de
   confiabilidade.

## Resposta curta para "por que uma rede neural?"

> A rede foi tratada como hipótese, não como premissa. Comparei seu
> ganho em padrões temporais não lineares contra métodos mais simples,
> usando split temporal, falsos alarmes e antecedência como critérios
> operacionais.

## Se a API/banco estiver fora do ar durante a demonstração

A interface deve degradar para o estado `model_unavailable` ou exibir
erro de carregamento sem quebrar (testado no Marco 8). Nesse caso,
usar como plano B os relatórios estáticos em `docs/resultados.md` e
`docs/protocolo-de-avaliacao.md`, ou rodar a API localmente
(`README.md`, seção "Banco de dados e API").
