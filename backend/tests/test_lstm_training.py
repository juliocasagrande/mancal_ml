from pathlib import Path

import numpy as np

from app.training.train_lstm import run_training

TINY_CONFIG = {
    "hidden_size": 4,
    "latent_size": 2,
    "learning_rate": 0.01,
    "batch_size": 8,
    "max_epochs": 3,
    "patience": 2,
    "seed": 0,
    "threshold_percentile": 95,
}


def _synthetic_windows(n: int, window_size: int, n_features: int, seed: int) -> np.ndarray:
    rng = np.random.default_rng(seed)
    return rng.normal(size=(n, window_size, n_features)).astype(np.float32)


def test_training_produces_all_expected_artifacts(tmp_path: Path) -> None:
    train_windows = _synthetic_windows(40, 8, 3, seed=1)
    val_windows = _synthetic_windows(10, 8, 3, seed=2)
    out_dir = tmp_path / "artifacts"

    result = run_training(TINY_CONFIG, train_windows, val_windows, out_dir)

    assert (out_dir / "model.pt").exists()
    assert (out_dir / "signal_scaler.joblib").exists()
    assert (out_dir / "config.json").exists()
    assert result.epochs_run <= TINY_CONFIG["max_epochs"]
    assert result.n_parameters > 0
    assert result.threshold >= 0


def test_scaler_fitted_only_on_train_windows(tmp_path: Path) -> None:
    train_windows = _synthetic_windows(40, 8, 3, seed=1) + 100  # deslocado
    val_windows = _synthetic_windows(10, 8, 3, seed=2)  # escala diferente, não deve influenciar o scaler
    out_dir = tmp_path / "artifacts"

    run_training(TINY_CONFIG, train_windows, val_windows, out_dir)

    import joblib

    scaler = joblib.load(out_dir / "signal_scaler.joblib")
    # A média aprendida deve refletir o deslocamento do treino (~100), não a validação (~0).
    assert all(abs(m - 100) < 10 for m in scaler.mean_)
