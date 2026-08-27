"""Pipeline temporal do Marco 2: limpeza -> split -> janelas -> atributos -> scaler.

Uso:
    .\\.venv\\Scripts\\python.exe backend\\scripts\\build_dataset.py

Lê os 6 arquivos G1 de `data/raw/`, produz:
    data/interim/g1_clean.csv           — série limpa e concatenada, com split
    data/interim/ingestion_report.json  — relatório de qualidade da execução
    data/processed/windows_<split>.npz  — janelas brutas por split
    data/processed/features_<split>.csv — atributos derivados por janela
    artifacts/scaler_v1.joblib          — scaler ajustado somente no treino
"""

from pathlib import Path

import numpy as np
import pandas as pd

from app.features.engineering import FEATURE_SET_VERSION, compute_window_features
from app.features.scaling import fit_scaler, save_scaler
from app.features.splits import TEST_FILES, TRAIN_FILES, VALIDATION_FILES, assign_split
from app.features.windows import make_windows
from app.ingestion.loader import load_raw_g1_file
from app.ingestion.quality import build_ingestion_run_report, save_report
from app.ingestion.schema import MODELING_COLUMNS

ROOT = Path(__file__).resolve().parents[2]
RAW_DIR = ROOT / "data" / "raw"
INTERIM_DIR = ROOT / "data" / "interim"
PROCESSED_DIR = ROOT / "data" / "processed"
ARTIFACT_DIR = ROOT / "artifacts"
MANIFEST_PATH = ROOT / "data" / "dataset_manifest.json"

PIPELINE_VERSION = "marco2-v1"
DATASET_VERSION = "2022-10-06-v1"

WINDOW_SIZE = 36  # 36 * 10min = 6 horas
STRIDE = 6  # 6 * 10min = 1 hora


def main() -> None:
    g1_files = TRAIN_FILES + VALIDATION_FILES + TEST_FILES
    frames, reports = [], []
    for name in g1_files:
        df, report = load_raw_g1_file(RAW_DIR / name)
        frames.append(df)
        reports.append(report)

    full = pd.concat(frames, ignore_index=True)
    full = assign_split(full)

    INTERIM_DIR.mkdir(parents=True, exist_ok=True)
    full.to_csv(INTERIM_DIR / "g1_clean.csv", index=False)

    ingestion_report = build_ingestion_run_report(
        dataset_version=DATASET_VERSION,
        manifest_path=MANIFEST_PATH,
        file_reports=reports,
        pipeline_version=PIPELINE_VERSION,
    )
    save_report(ingestion_report, INTERIM_DIR / "ingestion_report.json")
    print(f"Ingestão: {ingestion_report['row_count']} linhas, {len(g1_files)} arquivos")

    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)

    train_features = None
    scaler = None

    for split_name in ("train", "validation", "test"):
        split_df = full[full["split"] == split_name]
        windows = make_windows(split_df, MODELING_COLUMNS, WINDOW_SIZE, STRIDE)

        np.savez(
            PROCESSED_DIR / f"windows_{split_name}.npz",
            values=windows.values,
            window_start=np.array([str(t) for t in windows.window_start]),
            window_end=np.array([str(t) for t in windows.window_end]),
            source_file=np.array(windows.source_file),
        )

        derived, names = compute_window_features(windows.values, MODELING_COLUMNS)

        if split_name == "train":
            scaler = fit_scaler(derived)
            train_features = derived

        features_df = pd.DataFrame(derived, columns=names)
        features_df.insert(0, "window_end", windows.window_end)
        features_df.insert(0, "window_start", windows.window_start)
        features_df.insert(0, "source_file", windows.source_file)
        features_df.to_csv(PROCESSED_DIR / f"features_{split_name}.csv", index=False)

        print(f"{split_name}: {len(windows.window_start)} janelas, feature_set={FEATURE_SET_VERSION}")

    assert scaler is not None and train_features is not None
    save_scaler(scaler, ARTIFACT_DIR / "scaler_v1.joblib")
    print(
        f"Scaler ajustado apenas no treino ({train_features.shape[0]} janelas) e salvo em "
        "artifacts/scaler_v1.joblib"
    )


if __name__ == "__main__":
    main()
