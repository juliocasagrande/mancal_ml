"""Inferência da LSTM Autoencoder em processo separado do treino.

Uso:
    .\\.venv\\Scripts\\python.exe backend\\scripts\\score_lstm.py \\
        --artifacts-dir artifacts\\lstm_autoencoder_v1 --npz data\\processed\\windows_test.npz

Imprime uma linha JSON com a lista de scores de erro de reconstrução —
usado tanto para inferência real quanto pelo teste de reprodutibilidade
(backend/tests/test_lstm_reproducibility.py), que compara o resultado
deste processo com o calculado dentro do processo de treino.
"""

import argparse
import json
from pathlib import Path

import numpy as np

from app.inference.lstm_inference import load_artifacts, score_windows


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--artifacts-dir", type=Path, required=True)
    parser.add_argument("--npz", type=Path, required=True)
    args = parser.parse_args()

    model, scaler, _config = load_artifacts(args.artifacts_dir)
    windows = np.load(args.npz)["values"]
    scores = score_windows(model, scaler, windows)

    print(json.dumps(scores.tolist()))


if __name__ == "__main__":
    main()
