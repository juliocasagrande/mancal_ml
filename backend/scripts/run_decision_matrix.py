"""Marco 5: matriz de decisão ponderada e escolha transparente do
modelo campeão (Seção 9.4 do blueprint).

Pré-requisito: build_dataset.py, run_baselines.py e train_lstm.py já
executados.

Uso:
    .\\.venv\\Scripts\\python.exe backend\\scripts\\run_decision_matrix.py
"""

import json
import time
from pathlib import Path

import numpy as np
import pandas as pd

from app.evaluation.decision_matrix import DEFAULT_WEIGHTS, compute_decision_matrix
from app.evaluation.labels import build_proxy_labels
from app.evaluation.metrics import compute_event_metrics, detection_delay_windows
from app.features.cleaning import sanitize_features
from app.inference.lstm_inference import load_artifacts, score_windows
from app.models.baseline import RobustZScoreBaseline
from app.models.isolation_forest_model import IsolationForestModel

ROOT = Path(__file__).resolve().parents[2]
PROCESSED_DIR = ROOT / "data" / "processed"
ARTIFACTS_DIR = ROOT / "artifacts"
DOCS_DIR = ROOT / "docs"
METADATA_COLUMNS = ["source_file", "window_start", "window_end"]
STRIDE_HOURS = 1.0
VALIDATION_PERCENTILE = 99

# Critérios qualitativos (0-1), justificados em docs/resultados.md —
# hipótese operacional explícita, não medida diretamente dos dados.
QUALITATIVE_SCORES = {
    "baseline_zscore": {"robustness": 0.5, "explainability": 1.0},
    "isolation_forest": {"robustness": 0.6, "explainability": 0.4},
    "lstm_autoencoder": {"robustness": 0.7, "explainability": 0.7},
}


def feature_matrix(df: pd.DataFrame) -> np.ndarray:
    return sanitize_features(df.drop(columns=METADATA_COLUMNS).to_numpy(dtype=float))


def measure_latency_ms(score_fn, sample: np.ndarray, n_repeats: int = 50) -> tuple[float, float]:
    times = []
    for _ in range(n_repeats):
        start = time.perf_counter()
        score_fn(sample)
        times.append((time.perf_counter() - start) * 1000)
    return float(np.percentile(times, 50)), float(np.percentile(times, 95))


def main() -> None:
    train_df = pd.read_csv(PROCESSED_DIR / "features_train.csv")
    val_df = pd.read_csv(PROCESSED_DIR / "features_validation.csv")
    test_df = pd.read_csv(PROCESSED_DIR / "features_test.csv")
    test_windows = np.load(PROCESSED_DIR / "windows_test.npz")["values"]

    x_train, x_val, x_test = feature_matrix(train_df), feature_matrix(val_df), feature_matrix(test_df)

    train_median_power = train_df["generator_power__mean"].median()
    labels = build_proxy_labels(test_df["generator_power__mean"].to_numpy(), train_median_power)

    baseline = RobustZScoreBaseline().fit(x_train)
    iforest = IsolationForestModel().fit(x_train)
    lstm_model, lstm_scaler, lstm_config = load_artifacts(ARTIFACTS_DIR / "lstm_autoencoder_v1")

    criteria = {}

    for name, model in (("baseline_zscore", baseline), ("isolation_forest", iforest)):
        val_scores = model.score(x_val)
        threshold = float(np.percentile(val_scores, VALIDATION_PERCENTILE))
        test_scores = model.score(x_test)
        predictions = test_scores >= threshold

        event_metrics = compute_event_metrics(predictions, labels, STRIDE_HOURS)
        delay = detection_delay_windows(predictions, labels)
        p50, p95 = measure_latency_ms(model.score, x_test[:1])

        criteria[name] = {
            "event_recall": event_metrics.detection_rate,
            "false_alarms_per_day": event_metrics.false_alarms_per_day,
            "detection_delay_windows": delay,
            "latency_p95_ms": p95,
            **QUALITATIVE_SCORES[name],
        }

    lstm_threshold = lstm_config["threshold"]
    lstm_scores = score_windows(lstm_model, lstm_scaler, test_windows)
    lstm_predictions = lstm_scores >= lstm_threshold
    lstm_event_metrics = compute_event_metrics(lstm_predictions, labels, STRIDE_HOURS)
    lstm_delay = detection_delay_windows(lstm_predictions, labels)
    _, lstm_p95 = measure_latency_ms(lambda w: score_windows(lstm_model, lstm_scaler, w), test_windows[:1])

    criteria["lstm_autoencoder"] = {
        "event_recall": lstm_event_metrics.detection_rate,
        "false_alarms_per_day": lstm_event_metrics.false_alarms_per_day,
        "detection_delay_windows": lstm_delay,
        "latency_p95_ms": lstm_p95,
        **QUALITATIVE_SCORES["lstm_autoencoder"],
    }

    breakdown = compute_decision_matrix(criteria, DEFAULT_WEIGHTS)
    ranking = sorted(breakdown.items(), key=lambda kv: kv[1]["weighted_score"], reverse=True)

    print("=== Matriz de decisão (Seção 9.4 do blueprint) ===")
    for name, info in ranking:
        print(f"{name}: score ponderado = {info['weighted_score']:.3f}")
        for criterion, raw in info["raw_criteria"].items():
            print(f"    {criterion}: {raw:.4f} (peso {DEFAULT_WEIGHTS[criterion]})")

    champion = ranking[0][0]
    print(f"\nModelo campeão: {champion}")

    out_path = ROOT / "data" / "interim" / "decision_matrix.json"
    out_path.write_text(
        json.dumps({"weights": DEFAULT_WEIGHTS, "breakdown": breakdown, "champion": champion}, indent=2),
        encoding="utf-8",
    )
    print(f"Relatório salvo em {out_path}")


if __name__ == "__main__":
    main()
