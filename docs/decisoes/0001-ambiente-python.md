# ADR 0001 — Versão do Python no ambiente local

## Contexto

O blueprint do projeto recomenda Python 3.11 ou 3.12 (64 bits) pela
compatibilidade de wheels binários no Windows, especialmente para PyTorch
CPU (Marco 4). A auditoria do Marco 0 encontrou apenas Python 3.14.3 (64
bits) disponível via `py -0p` na máquina de desenvolvimento.

## Decisão

Seguir com Python 3.14 para os Marcos 0 e 1, que dependem apenas de
Pandas/NumPy/FastAPI — bibliotecas com wheels disponíveis para 3.14 no
momento da implementação (2026-08-26).

## Consequência e ponto de reavaliação

Antes do Marco 4 (LSTM Autoencoder), verificar se há wheel de `torch` CPU
compatível com Python 3.14 no Windows. Se não houver, instalar Python
3.12 em paralelo (sem privilégio de administrador, via instalador
`python.org` no modo "Install for me only" ou via `py` launcher) e criar
um `.venv` dedicado ao backend com essa versão, sem alterar o Python
usado pelo restante do sistema do usuário.
