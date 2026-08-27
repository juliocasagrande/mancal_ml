"""Inferência da LSTM Autoencoder a partir de artefatos persistidos.

Carrega modelo, scaler de sinal e config de um diretório de artefatos —
sem qualquer estado em memória do processo de treino. Usado tanto pela
API de inferência (Marco 6) quanto pelo teste de reprodutibilidade em
processo separado (Marco 4).
"""

import json
from pathlib import Path

import joblib
import numpy as np
import torch

from app.models.lstm_autoencoder import LSTMAutoencoder, reconstruction_error


def load_artifacts(artifacts_dir: Path) -> tuple[LSTMAutoencoder, object, dict]:
    config = json.loads((artifacts_dir / "config.json").read_text(encoding="utf-8"))
    scaler = joblib.load(artifacts_dir / "signal_scaler.joblib")

    model = LSTMAutoencoder(
        n_features=config["n_features"],
        hidden_size=config["hidden_size"],
        latent_size=config["latent_size"],
    )
    state_dict = torch.load(artifacts_dir / "model.pt", map_location="cpu")
    model.load_state_dict(state_dict)
    model.eval()

    return model, scaler, config


def score_windows(model: LSTMAutoencoder, scaler, windows: np.ndarray) -> np.ndarray:
    n, window_size, n_features = windows.shape
    flat = windows.reshape(n * window_size, n_features)
    scaled = scaler.transform(flat).reshape(n, window_size, n_features)

    tensor = torch.tensor(scaled, dtype=torch.float32)
    with torch.no_grad():
        reconstructed = model(tensor)
        errors = reconstruction_error(tensor, reconstructed)
    return errors.numpy()
