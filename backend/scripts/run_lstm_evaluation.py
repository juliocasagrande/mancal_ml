"""Marco 4/5: avalia a LSTM Autoencoder no split de teste com o mesmo
protocolo do Marco 3 (rótulo-proxy, métricas por janela e por evento),
para permitir comparação direta com os baselines.

Uso:
    .\\.venv\\Scripts\\python.exe backend\\scripts\\run_lstm_evaluation.py
"""

import json
from pathlib import Path

import numpy as np
import pandas as pd

from app.evaluation.labels import build_proxy_labels
from app.evaluation.metrics import compute_event_metrics, compute_window_metrics
from app.inference.lstm_inference import load_artifacts, score_windows

ROOT = Path(__file__).resolve().parents[2]
PROCESSED_DIR = ROOT / "data" / "processed"
ARTIFACTS_DIR = ROOT / "artifacts" / "lstm_autoencoder_v1"
STRIDE_HOURS = 1.0


def main() -> None:
    train_df = pd.read_csv(PROCESSED_DIR / "features_train.csv")
    test_df = pd.read_csv(PROCESSED_DIR / "features_test.csv")
    test_windows = np.load(PROCESSED_DIR / "windows_test.npz")["values"]

    model, scaler, config = load_artifacts(ARTIFACTS_DIR)
    scores = score_windows(model, scaler, test_windows)
    threshold = config["threshold"]
    predictions = scores >= threshold

    train_median_power = train_df["generator_power__mean"].median()
    labels = build_proxy_labels(test_df["generator_power__mean"].to_numpy(), train_median_power)

    window_metrics = compute_window_metrics(scores, labels, threshold)
    event_metrics = compute_event_metrics(predictions, labels, STRIDE_HOURS)

    print("=== lstm_autoencoder ===")
    print(f"limiar (validação, percentil {config['threshold_percentile']}): {threshold:.4f}")
    print(f"parâmetros: {config['n_parameters']} | épocas: {config['epochs_run']} | "
          f"tempo de treino: {config['train_seconds']:.1f}s")
    print(f"janela: precision={window_metrics.precision:.3f} recall={window_metrics.recall:.3f} "
          f"f1={window_metrics.f1:.3f} pr_auc={window_metrics.pr_auc:.3f}")
    print(f"evento: {event_metrics.n_detected_events}/{event_metrics.n_true_events} detectados "
          f"({event_metrics.detection_rate:.1%}), "
          f"{event_metrics.n_false_alarm_events} falso-alarmes "
          f"({event_metrics.false_alarms_per_day:.2f}/dia)")

    report = {
        "model": "lstm_autoencoder_v1",
        "config": config,
        "window_metrics": vars(window_metrics),
        "event_metrics": vars(event_metrics),
    }
    out_path = ROOT / "data" / "interim" / "evaluation_report_lstm.json"
    out_path.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\nRelatório salvo em {out_path}")


if __name__ == "__main__":
    main()
