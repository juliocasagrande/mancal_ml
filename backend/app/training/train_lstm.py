"""Treino da LSTM Autoencoder (Marco 4).

Regras seguidas (Seção 9.3 do blueprint):
- treino somente com dados saudáveis (split de treino);
- scaler de sinal ajustado exclusivamente no treino;
- seed fixa e early stopping por perda de reconstrução na validação;
- artefatos (pesos, scaler, config, limiar) persistidos juntos, de forma
  a permitir reprodução em processo separado (ver
  backend/scripts/score_lstm.py e teste de reprodutibilidade).
"""

import json
import random
import time
from dataclasses import asdict, dataclass
from pathlib import Path

import joblib
import numpy as np
import torch
from sklearn.preprocessing import StandardScaler
from torch import nn
from torch.utils.data import DataLoader, TensorDataset

from app.models.lstm_autoencoder import LSTMAutoencoder, reconstruction_error

MODEL_ARCHITECTURE_VERSION = "lstm_autoencoder_v1"


@dataclass
class TrainingResult:
    epochs_run: int
    best_val_loss: float
    n_parameters: int
    train_seconds: float
    threshold: float


def set_seed(seed: int) -> None:
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)


def _fit_signal_scaler(train_windows: np.ndarray) -> StandardScaler:
    n, window_size, n_features = train_windows.shape
    flat = train_windows.reshape(n * window_size, n_features)
    scaler = StandardScaler().fit(flat)
    return scaler


def _apply_scaler(windows: np.ndarray, scaler: StandardScaler) -> np.ndarray:
    n, window_size, n_features = windows.shape
    flat = windows.reshape(n * window_size, n_features)
    scaled = scaler.transform(flat)
    return scaled.reshape(n, window_size, n_features)


def run_training(
    config: dict,
    train_windows: np.ndarray,
    val_windows: np.ndarray,
    out_dir: Path,
) -> TrainingResult:
    set_seed(config["seed"])

    scaler = _fit_signal_scaler(train_windows)
    train_scaled = _apply_scaler(train_windows, scaler)
    val_scaled = _apply_scaler(val_windows, scaler)

    n_features = train_windows.shape[2]
    model = LSTMAutoencoder(
        n_features=n_features,
        hidden_size=config["hidden_size"],
        latent_size=config["latent_size"],
    )
    optimizer = torch.optim.Adam(model.parameters(), lr=config["learning_rate"])
    loss_fn = nn.MSELoss()

    train_tensor = torch.tensor(train_scaled, dtype=torch.float32)
    val_tensor = torch.tensor(val_scaled, dtype=torch.float32)
    loader = DataLoader(TensorDataset(train_tensor), batch_size=config["batch_size"], shuffle=True)

    best_val_loss = float("inf")
    best_state = None
    epochs_without_improvement = 0
    start = time.time()
    epochs_run = 0

    for epoch in range(config["max_epochs"]):
        epochs_run = epoch + 1
        model.train()
        for (batch,) in loader:
            optimizer.zero_grad()
            reconstructed = model(batch)
            loss = loss_fn(reconstructed, batch)
            loss.backward()
            optimizer.step()

        model.eval()
        with torch.no_grad():
            val_reconstructed = model(val_tensor)
            val_loss = loss_fn(val_reconstructed, val_tensor).item()

        if val_loss < best_val_loss:
            best_val_loss = val_loss
            best_state = {k: v.clone() for k, v in model.state_dict().items()}
            epochs_without_improvement = 0
        else:
            epochs_without_improvement += 1
            if epochs_without_improvement >= config["patience"]:
                break

    assert best_state is not None
    model.load_state_dict(best_state)
    train_seconds = time.time() - start

    model.eval()
    with torch.no_grad():
        val_errors = reconstruction_error(val_tensor, model(val_tensor)).numpy()
    threshold = float(np.percentile(val_errors, config["threshold_percentile"]))

    out_dir.mkdir(parents=True, exist_ok=True)
    torch.save(model.state_dict(), out_dir / "model.pt")
    joblib.dump(scaler, out_dir / "signal_scaler.joblib")

    result = TrainingResult(
        epochs_run=epochs_run,
        best_val_loss=best_val_loss,
        n_parameters=model.n_parameters(),
        train_seconds=train_seconds,
        threshold=threshold,
    )
    full_config = {
        "architecture_version": MODEL_ARCHITECTURE_VERSION,
        "n_features": n_features,
        "window_size": train_windows.shape[1],
        **config,
        **asdict(result),
    }
    (out_dir / "config.json").write_text(json.dumps(full_config, indent=2), encoding="utf-8")

    return result
