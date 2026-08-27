"""Extensão pós-MVP (Seção 20 do blueprint): detecção de drift de dados.

Compara a distribuição dos atributos derivados de cada mês de validação e
teste contra o treino (PSI por atributo — `app/evaluation/drift.py`).
Não depende de rótulo nem de modelo: mede desvio de regime operacional.

Pré-requisito: `build_dataset.py` já executado.

Uso:
    .\\.venv\\Scripts\\python.exe backend\\scripts\\run_drift_report.py
"""

import json
from dataclasses import asdict
from pathlib import Path

import numpy as np
import pandas as pd

from app.evaluation.drift import compute_drift_report
from app.features.cleaning import sanitize_features

ROOT = Path(__file__).resolve().parents[2]
PROCESSED_DIR = ROOT / "data" / "processed"

METADATA_COLUMNS = ["source_file", "window_start", "window_end"]


def load_split(name: str) -> pd.DataFrame:
    return pd.read_csv(PROCESSED_DIR / f"features_{name}.csv")


def feature_matrix(df: pd.DataFrame) -> np.ndarray:
    return sanitize_features(df.drop(columns=METADATA_COLUMNS).to_numpy(dtype=float))


def main() -> None:
    train_df = load_split("train")
    val_df = load_split("validation")
    test_df = load_split("test")

    feature_names = [c for c in train_df.columns if c not in METADATA_COLUMNS]
    x_train = feature_matrix(train_df)

    periods: list[dict] = []
    for split_name, df in [("validation", val_df), ("test", test_df)]:
        for source_file, group in df.groupby("source_file", sort=False):
            current = feature_matrix(group)
            report = compute_drift_report(x_train, current, feature_names)
            top_features = sorted(report.per_feature, key=lambda f: f.psi, reverse=True)[:5]
            periods.append(
                {
                    "split": split_name,
                    "period": source_file,
                    "reference_n": report.reference_n,
                    "current_n": report.current_n,
                    "overall_psi": report.overall_psi,
                    "severity": report.severity,
                    "top_features": [asdict(f) for f in top_features],
                }
            )
            print(f"{source_file} ({split_name}): PSI médio={report.overall_psi:.3f} ({report.severity})")

    output = {
        "reference": "treino (June.csv + July.csv)",
        "method": "Population Stability Index (PSI) por atributo, decis do treino",
        "severity_thresholds": {"none": "< 0.1", "moderate": "0.1 – 0.25", "significant": ">= 0.25"},
        "periods": periods,
    }

    out_path = ROOT / "data" / "interim" / "drift_report.json"
    out_path.write_text(json.dumps(output, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\nRelatório salvo em {out_path}")


if __name__ == "__main__":
    main()
