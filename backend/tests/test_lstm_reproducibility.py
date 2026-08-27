"""Marco 4 — critério de aceite: 'inferência reproduz o resultado do
experimento em processo separado'. Treina um modelo minúsculo, salva os
artefatos, e compara o score calculado dentro do processo de teste com o
score calculado por `backend/scripts/score_lstm.py` rodando como um
subprocesso Python totalmente separado (novo interpretador, sem estado
compartilhado).
"""

import json
import os
import subprocess
import sys
from pathlib import Path

import numpy as np

from app.inference.lstm_inference import load_artifacts, score_windows
from app.training.train_lstm import run_training

BACKEND_DIR = Path(__file__).resolve().parents[1]

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


def test_subprocess_inference_matches_in_process_inference(tmp_path: Path) -> None:
    rng = np.random.default_rng(7)
    train_windows = rng.normal(size=(40, 8, 3)).astype(np.float32)
    val_windows = rng.normal(size=(10, 8, 3)).astype(np.float32)
    test_windows = rng.normal(size=(6, 8, 3)).astype(np.float32)

    artifacts_dir = tmp_path / "artifacts"
    run_training(TINY_CONFIG, train_windows, val_windows, artifacts_dir)

    npz_path = tmp_path / "windows_test.npz"
    np.savez(npz_path, values=test_windows)

    model, scaler, _config = load_artifacts(artifacts_dir)
    in_process_scores = score_windows(model, scaler, test_windows)

    env = os.environ.copy()
    env["PYTHONPATH"] = str(BACKEND_DIR)
    result = subprocess.run(
        [
            sys.executable,
            str(BACKEND_DIR / "scripts" / "score_lstm.py"),
            "--artifacts-dir",
            str(artifacts_dir),
            "--npz",
            str(npz_path),
        ],
        cwd=BACKEND_DIR,
        env=env,
        capture_output=True,
        text=True,
        check=True,
    )
    subprocess_scores = np.array(json.loads(result.stdout))

    np.testing.assert_allclose(subprocess_scores, in_process_scores, rtol=1e-5, atol=1e-6)
