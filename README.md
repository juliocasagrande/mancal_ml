# hydro-bearing-predictive-maintenance

> Sistema de monitoramento de condição que compara baselines estatísticos,
> modelos clássicos e uma rede LSTM para detectar degradação em um mancal de
> turbina hidráulica, com avaliação temporal, índice de saúde e
> explicabilidade operacional.

**Status:** em construção — Marcos 0 a 4 concluídos (repositório,
auditoria do dataset, pipeline temporal, baselines e LSTM Autoencoder).
Resultados comparativos em `docs/resultados.md`. Este README será
reescrito com resultados, screenshots e arquitetura ao final (ver
`docs/decisoes/`).

O sistema é um apoio à decisão. Não emite comandos para equipamentos nem se
apresenta como solução certificada para operação real.

## Dataset

Bearing Vibration Dataset of a Hydropower Project (Yasir Saleem Afridi,
[DOI 10.6084/m9.figshare.21290895.v1](https://doi.org/10.6084/m9.figshare.21290895.v1),
CC BY 4.0). Detalhes em [`data/README.md`](data/README.md).

## Ambiente de desenvolvimento (Windows, sem admin, sem Docker)

```powershell
python --version
node --version
npm --version
git --version
```

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -r backend\requirements.txt
```

Se o caminho do projeto for longo (ex.: dentro do OneDrive), a instalação
do `torch` pode falhar com `WinError 206` (caminho excede 260
caracteres). Nesse caso, ver `docs/decisoes/0003-instalacao-pytorch-caminho-longo.md`:

```powershell
.\.venv\Scripts\python.exe -m pip install torch --index-url https://download.pytorch.org/whl/cpu --target "C:\tmp\pylibs" --no-deps
echo C:\tmp\pylibs > .venv\Lib\site-packages\_torch_external.pth
```

```powershell
cd frontend
npm install
```

## Pipeline de dados (Marco 1 e 2)

```powershell
.\.venv\Scripts\python.exe backend\scripts\download_dataset.py
.\.venv\Scripts\python.exe backend\scripts\audit_dataset.py
.\.venv\Scripts\python.exe backend\scripts\build_dataset.py
```

Gera `data/interim/g1_clean.csv`, `data/interim/ingestion_report.json`,
janelas e atributos por split em `data/processed/` e o scaler treinado em
`artifacts/scaler_v1.joblib`. Ver `docs/formulacao-do-problema.md` para a
definição do split temporal e a tarefa de ML escolhida.

```powershell
.\.venv\Scripts\python.exe backend\scripts\run_baselines.py
```

Compara baseline estatístico e Isolation Forest e grava
`data/interim/evaluation_report_marco3.json`. Resultados discutidos em
`docs/resultados.md`.

```powershell
.\.venv\Scripts\python.exe backend\scripts\train_lstm.py --config configs\lstm_autoencoder.yaml
.\.venv\Scripts\python.exe backend\scripts\run_lstm_evaluation.py
```

Treina a LSTM Autoencoder (CPU, ~35s) e avalia no mesmo protocolo dos
baselines. Artefatos em `artifacts/lstm_autoencoder_v1/` (pesos, scaler
de sinal e config com o limiar escolhido na validação).

## Testes

```powershell
.\.venv\Scripts\python.exe -m pytest backend\tests -q
cd frontend; npm run test
```

## Estrutura do repositório

Ver árvore completa em [`PROJETO_01_MANUTENCAO_PREDITIVA_UHE.md`](PROJETO_01_MANUTENCAO_PREDITIVA_UHE.md).
Documentação de progresso em [`docs/`](docs/).

## Licença

Código sob licença MIT (ver `LICENSE`). Dataset sob CC BY 4.0 — ver
`data/README.md` e `CITATION.cff` para atribuição correta.
