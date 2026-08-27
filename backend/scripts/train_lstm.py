"""Marco 4: treino da LSTM Autoencoder.

Uso:
    .\\.venv\\Scripts\\python.exe backend\\scripts\\train_lstm.py --config configs\\lstm_autoencoder.yaml

Pré-requisito: `build_dataset.py` já executado (gera
`data/processed/windows_{train,validation}.npz`).
"""

import argparse
from pathlib import Path

import numpy as np
import yaml

from app.training.train_lstm import run_training

ROOT = Path(__file__).resolve().parents[2]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, default=ROOT / "configs" / "lstm_autoencoder.yaml")
    parser.add_argument("--processed-dir", type=Path, default=ROOT / "data" / "processed")
    parser.add_argument("--out-dir", type=Path, default=ROOT / "artifacts" / "lstm_autoencoder_v1")
    args = parser.parse_args()

    config = yaml.safe_load(args.config.read_text(encoding="utf-8"))

    train_windows = np.load(args.processed_dir / "windows_train.npz")["values"]
    val_windows = np.load(args.processed_dir / "windows_validation.npz")["values"]

    print(f"Treino: {train_windows.shape}, Validação: {val_windows.shape}")
    result = run_training(config, train_windows, val_windows, args.out_dir)

    print(f"Épocas: {result.epochs_run} | melhor loss de validação: {result.best_val_loss:.6f}")
    print(f"Parâmetros: {result.n_parameters} | tempo de treino: {result.train_seconds:.1f}s")
    print(f"Limiar (percentil {config['threshold_percentile']} da validação): {result.threshold:.6f}")
    print(f"Artefatos salvos em {args.out_dir}")


if __name__ == "__main__":
    main()
