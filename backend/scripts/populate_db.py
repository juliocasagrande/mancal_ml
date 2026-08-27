"""Marco 6: popula o Railway PostgreSQL a partir dos artefatos locais do
pipeline (dataset, ingestão, sinal limpo, modelos, avaliações e uma
amostra de previsões/alertas para demonstração).

Pré-requisito: build_dataset.py, run_baselines.py, train_lstm.py e
run_decision_matrix.py já executados; migrações Alembic aplicadas
(`alembic upgrade head`).

Uso:
    .\\.venv\\Scripts\\python.exe backend\\scripts\\populate_db.py
"""

import json
import subprocess
from pathlib import Path

import numpy as np
import pandas as pd

from app.db.models import Alert, Dataset, EvaluationRun, IngestionRun, ModelVersion, PredictionRun, SignalSample
from app.db.session import get_session_factory
from app.ingestion.schema import VALUE_COLUMNS
from app.inference.lstm_inference import load_artifacts, score_windows

ROOT = Path(__file__).resolve().parents[2]
INTERIM_DIR = ROOT / "data" / "interim"
PROCESSED_DIR = ROOT / "data" / "processed"
ARTIFACTS_DIR = ROOT / "artifacts"

DATASET_SOURCE_URL = "https://figshare.com/articles/dataset/Bearing_Vibration_Dataset_of_a_Hydropower_Project/21290895"
DATASET_DOI = "10.6084/m9.figshare.21290895.v1"


def _git_commit() -> str | None:
    try:
        out = subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True, text=True, check=True, cwd=ROOT)
        return out.stdout.strip()
    except Exception:
        return None


def main() -> None:
    ingestion_report = json.loads((INTERIM_DIR / "ingestion_report.json").read_text(encoding="utf-8"))
    clean_df = pd.read_csv(INTERIM_DIR / "g1_clean.csv", parse_dates=["timestamp"])

    baselines_report = json.loads((INTERIM_DIR / "evaluation_report_marco3.json").read_text(encoding="utf-8"))
    lstm_eval_report = json.loads((INTERIM_DIR / "evaluation_report_lstm.json").read_text(encoding="utf-8"))
    decision = json.loads((INTERIM_DIR / "decision_matrix.json").read_text(encoding="utf-8"))
    champion_name = decision["champion"]

    Session = get_session_factory()
    with Session() as db:
        db.query(Alert).delete()
        db.query(PredictionRun).delete()
        db.query(EvaluationRun).delete()
        db.query(ModelVersion).delete()
        db.query(SignalSample).delete()
        db.query(IngestionRun).delete()
        db.query(Dataset).delete()
        db.commit()

        dataset = Dataset(
            name="Bearing Vibration Dataset of a Hydropower Project",
            source_url=DATASET_SOURCE_URL,
            license="CC-BY-4.0",
            version=DATASET_DOI,
            time_start=clean_df["timestamp"].min(),
            time_end=clean_df["timestamp"].max(),
            dataset_metadata={
                "unit": "G1",
                "author": "Yasir Saleem Afridi",
                "scope_note": "Apenas os 6 arquivos mensais da unidade G1 — ver docs/formulacao-do-problema.md",
            },
        )
        db.add(dataset)
        db.flush()

        db.add(
            IngestionRun(
                dataset_id=dataset.id,
                status="success",
                row_count=ingestion_report["row_count"],
                quality_report=ingestion_report,
                pipeline_version=ingestion_report["pipeline_version"],
            )
        )

        samples = [
            SignalSample(
                dataset_id=dataset.id,
                timestamp=row.timestamp,
                source_file=row.source_file,
                split=row.split,
                quality_flags={"has_missing": bool(row.has_missing)},
                **{col: (None if pd.isna(getattr(row, col)) else float(getattr(row, col))) for col in VALUE_COLUMNS},
            )
            for row in clean_df.itertuples(index=False)
        ]
        db.bulk_save_objects(samples)
        print(f"{len(samples)} amostras de sinal inseridas")

        model_versions = {}
        for name, report in (
            ("baseline_zscore", baselines_report["models"]["baseline_zscore"]),
            ("isolation_forest", baselines_report["models"]["isolation_forest"]),
        ):
            mv = ModelVersion(
                name=name,
                algorithm=name,
                artifact_path="(recalculado em runtime, não persistido em artifacts/)",
                dataset_version=DATASET_DOI,
                hyperparameters={},
                metrics=report["window_metrics"],
                status="active" if name == champion_name else "candidate",
                git_commit=_git_commit(),
            )
            db.add(mv)
            db.flush()
            model_versions[name] = mv
            db.add(
                EvaluationRun(
                    model_version_id=mv.id,
                    configuration={"threshold": report["threshold"]},
                    metrics=report["window_metrics"],
                    confusion_matrix={"matrix": report["window_metrics"]["confusion_matrix"]},
                )
            )

        lstm_config = lstm_eval_report["config"]
        mv_lstm = ModelVersion(
            name="lstm_autoencoder",
            algorithm="lstm_autoencoder",
            artifact_path=str((ARTIFACTS_DIR / "lstm_autoencoder_v1").relative_to(ROOT)),
            dataset_version=DATASET_DOI,
            feature_schema={"n_features": lstm_config["n_features"], "window_size": lstm_config["window_size"]},
            hyperparameters={k: lstm_config[k] for k in ("hidden_size", "latent_size", "learning_rate", "seed")},
            metrics=lstm_eval_report["window_metrics"],
            status="active" if champion_name == "lstm_autoencoder" else "candidate",
            git_commit=_git_commit(),
        )
        db.add(mv_lstm)
        db.flush()
        model_versions["lstm_autoencoder"] = mv_lstm
        db.add(
            EvaluationRun(
                model_version_id=mv_lstm.id,
                configuration={"threshold": lstm_config["threshold"]},
                metrics=lstm_eval_report["window_metrics"],
                confusion_matrix={"matrix": lstm_eval_report["window_metrics"]["confusion_matrix"]},
            )
        )

        # Amostra de previsões/alertas para demonstração: usa o modelo campeão
        # sobre o split de teste (Página 1/2 do frontend precisam de dados).
        champion_mv = model_versions[champion_name]
        test_windows_npz = np.load(PROCESSED_DIR / "windows_test.npz")
        window_starts = pd.to_datetime(test_windows_npz["window_start"])
        window_ends = pd.to_datetime(test_windows_npz["window_end"])

        if champion_name == "lstm_autoencoder":
            model, scaler, config = load_artifacts(ARTIFACTS_DIR / "lstm_autoencoder_v1")
            scores = score_windows(model, scaler, test_windows_npz["values"])
            threshold = config["threshold"]
        else:
            test_features_df = pd.read_csv(PROCESSED_DIR / "features_test.csv")
            from app.features.cleaning import sanitize_features
            from app.models.baseline import RobustZScoreBaseline
            from app.models.isolation_forest_model import IsolationForestModel

            train_features_df = pd.read_csv(PROCESSED_DIR / "features_train.csv")
            metadata_cols = ["source_file", "window_start", "window_end"]
            x_train = sanitize_features(train_features_df.drop(columns=metadata_cols).to_numpy(dtype=float))
            x_test = sanitize_features(test_features_df.drop(columns=metadata_cols).to_numpy(dtype=float))
            model = RobustZScoreBaseline().fit(x_train) if champion_name == "baseline_zscore" else IsolationForestModel().fit(x_train)
            scores = model.score(x_test)
            threshold = float(np.percentile(scores, 99))

        max_score = float(np.max(scores)) if len(scores) else 1.0
        for start, end, score in zip(window_starts, window_ends, scores):
            health_index = 100 * max(0.0, min(1.0, 1 - float(score) / max_score))
            state = "alert" if score >= threshold else ("attention" if score >= 0.7 * threshold else "normal")
            pr = PredictionRun(
                model_version_id=champion_mv.id,
                window_start=start,
                window_end=end,
                anomaly_score=float(score),
                health_index=health_index,
                state=state,
                feature_contributions={},
            )
            db.add(pr)
            if state == "alert":
                db.flush()
                db.add(
                    Alert(
                        prediction_run_id=pr.id,
                        severity="alert",
                        reason=(
                            "Score de anomalia acima do limiar calibrado na validação. "
                            "Rótulo-proxy — ver docs/formulacao-do-problema.md."
                        ),
                    )
                )

        db.commit()
        print(f"Modelo campeão marcado como ativo: {champion_name}")
        print(f"{len(window_starts)} previsões e alertas de demonstração inseridos")


if __name__ == "__main__":
    main()
