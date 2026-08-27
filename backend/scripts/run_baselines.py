"""Marco 3: baseline estatístico x Isolation Forest, com métricas
por janela e por evento sobre o split de teste.

Pré-requisito: `build_dataset.py` já executado (gera
`data/processed/features_{train,validation,test}.csv`).

Uso:
    .\\.venv\\Scripts\\python.exe backend\\scripts\\run_baselines.py
"""

import json
from pathlib import Path

import numpy as np
import pandas as pd

from app.evaluation.labels import build_proxy_labels
from app.evaluation.metrics import compute_event_metrics, compute_window_metrics
from app.features.cleaning import sanitize_features
from app.models.baseline import RobustZScoreBaseline
from app.models.isolation_forest_model import IsolationForestModel

ROOT = Path(__file__).resolve().parents[2]
PROCESSED_DIR = ROOT / "data" / "processed"
DOCS_DIR = ROOT / "docs"

METADATA_COLUMNS = ["source_file", "window_start", "window_end"]
VALIDATION_PERCENTILE = 99
STRIDE_HOURS = 1.0  # deve casar com STRIDE de build_dataset.py (6 * 10min)


def load_split(name: str) -> pd.DataFrame:
    return pd.read_csv(PROCESSED_DIR / f"features_{name}.csv")


def feature_matrix(df: pd.DataFrame) -> np.ndarray:
    return sanitize_features(df.drop(columns=METADATA_COLUMNS).to_numpy(dtype=float))


def main() -> None:
    train_df = load_split("train")
    val_df = load_split("validation")
    test_df = load_split("test")

    x_train = feature_matrix(train_df)
    x_val = feature_matrix(val_df)
    x_test = feature_matrix(test_df)

    baseline = RobustZScoreBaseline().fit(x_train)
    iforest = IsolationForestModel().fit(x_train)

    models = {"baseline_zscore": baseline, "isolation_forest": iforest}

    train_median_power = train_df["generator_power__mean"].median()
    test_labels = build_proxy_labels(test_df["generator_power__mean"].to_numpy(), train_median_power)

    report = {
        "validation_percentile_for_threshold": VALIDATION_PERCENTILE,
        "proxy_label_note": (
            "Rótulo-proxy baseado em baixa potência média por janela — NÃO é um "
            "rótulo de falha confirmado. Ver docs/formulacao-do-problema.md."
        ),
        "n_test_windows": len(test_df),
        "n_test_proxy_anomalous_windows": int(test_labels.sum()),
        "models": {},
    }

    for name, model in models.items():
        val_scores = model.score(x_val)
        threshold = float(np.percentile(val_scores, VALIDATION_PERCENTILE))

        test_scores = model.score(x_test)
        predictions = test_scores >= threshold

        window_metrics = compute_window_metrics(test_scores, test_labels, threshold)
        event_metrics = compute_event_metrics(predictions, test_labels, STRIDE_HOURS)

        report["models"][name] = {
            "threshold": threshold,
            "window_metrics": vars(window_metrics),
            "event_metrics": vars(event_metrics),
        }
        print(f"\n=== {name} ===")
        print(f"limiar (percentil {VALIDATION_PERCENTILE} da validação): {threshold:.4f}")
        print(f"janela: precision={window_metrics.precision:.3f} recall={window_metrics.recall:.3f} "
              f"f1={window_metrics.f1:.3f} pr_auc={window_metrics.pr_auc:.3f}")
        print(f"evento: {event_metrics.n_detected_events}/{event_metrics.n_true_events} detectados "
              f"({event_metrics.detection_rate:.1%}), "
              f"{event_metrics.n_false_alarm_events} falso-alarmes "
              f"({event_metrics.false_alarms_per_day:.2f}/dia)")

    out_path = ROOT / "data" / "interim" / "evaluation_report_marco3.json"
    out_path.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\nRelatório salvo em {out_path}")


if __name__ == "__main__":
    main()
