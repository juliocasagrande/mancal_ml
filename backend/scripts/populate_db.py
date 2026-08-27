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
import uuid
from pathlib import Path

import numpy as np
import pandas as pd
import torch

from app.db.models import Alert, Dataset, EvaluationRun, IngestionRun, ModelVersion, PredictionRun, SignalSample
from app.db.session import get_session_factory
from app.evaluation.explainability import baseline_feature_contribution, lstm_feature_contribution
from app.ingestion.schema import MODELING_COLUMNS, VALUE_COLUMNS
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
            metrics_with_curves = {**report["window_metrics"], "curves": report["curves"]}
            mv = ModelVersion(
                name=name,
                algorithm=name,
                artifact_path="(recalculado em runtime, não persistido em artifacts/)",
                dataset_version=DATASET_DOI,
                hyperparameters={"threshold": report["threshold"]},
                metrics=metrics_with_curves,
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
                    metrics=metrics_with_curves,
                    confusion_matrix={"matrix": report["window_metrics"]["confusion_matrix"]},
                )
            )

        lstm_config = lstm_eval_report["config"]
        lstm_metrics_with_curves = {**lstm_eval_report["window_metrics"], "curves": lstm_eval_report["curves"]}
        mv_lstm = ModelVersion(
            name="lstm_autoencoder",
            algorithm="lstm_autoencoder",
            artifact_path=str((ARTIFACTS_DIR / "lstm_autoencoder_v1").relative_to(ROOT)),
            dataset_version=DATASET_DOI,
            feature_schema={"n_features": lstm_config["n_features"], "window_size": lstm_config["window_size"]},
            hyperparameters={
                **{k: lstm_config[k] for k in ("hidden_size", "latent_size", "learning_rate", "seed")},
                "threshold": lstm_config["threshold"],
            },
            metrics=lstm_metrics_with_curves,
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
                metrics=lstm_metrics_with_curves,
                confusion_matrix={"matrix": lstm_eval_report["window_metrics"]["confusion_matrix"]},
            )
        )

        # Checkpoint: dataset, ingestão, sinal e modelos já persistidos.
        # Commitar aqui evita perder esse trabalho se o lote grande de
        # previsões abaixo falhar por instabilidade do proxy TCP do Railway
        # (já aconteceu — ver docs/decisoes/0005-interface-react-marco7.md).
        db.commit()
        print("Dataset, sinal e modelos persistidos")

        # Amostra de previsões/alertas para demonstração: usa o modelo campeão
        # sobre o split de teste (Página 1/2 do frontend precisam de dados).
        champion_mv = model_versions[champion_name]
        test_windows_npz = np.load(PROCESSED_DIR / "windows_test.npz")
        window_starts = pd.to_datetime(test_windows_npz["window_start"])
        window_ends = pd.to_datetime(test_windows_npz["window_end"])

        # feature_contributions por janela — Seção 11 do blueprint / Página 4
        # do frontend (Marco 7). Só implementado onde
        # app/evaluation/explainability.py oferece uma decomposição nativa:
        # LSTM (erro de reconstrução por canal) e baseline z-score (|z| por
        # atributo). Isolation Forest não decompõe nativamente por variável
        # (ver docs/resultados.md) — fica com {} nesse caso.
        contributions_list: list[dict[str, float]] = []

        if champion_name == "lstm_autoencoder":
            model, scaler, config = load_artifacts(ARTIFACTS_DIR / "lstm_autoencoder_v1")
            raw_windows = test_windows_npz["values"]
            scores = score_windows(model, scaler, raw_windows)
            threshold = config["threshold"]

            n, window_size, n_features = raw_windows.shape
            flat = raw_windows.reshape(n * window_size, n_features)
            scaled_windows = scaler.transform(flat).reshape(n, window_size, n_features)
            with torch.no_grad():
                reconstructed = model(torch.tensor(scaled_windows, dtype=torch.float32)).numpy()
            contributions_list = [
                lstm_feature_contribution(scaled_windows[i], reconstructed[i], MODELING_COLUMNS) for i in range(n)
            ]
        else:
            test_features_df = pd.read_csv(PROCESSED_DIR / "features_test.csv")
            from app.features.cleaning import sanitize_features
            from app.models.baseline import RobustZScoreBaseline
            from app.models.isolation_forest_model import IsolationForestModel

            train_features_df = pd.read_csv(PROCESSED_DIR / "features_train.csv")
            metadata_cols = ["source_file", "window_start", "window_end"]
            feature_names = [c for c in test_features_df.columns if c not in metadata_cols]
            x_train = sanitize_features(train_features_df.drop(columns=metadata_cols).to_numpy(dtype=float))
            x_test = sanitize_features(test_features_df.drop(columns=metadata_cols).to_numpy(dtype=float))
            model = RobustZScoreBaseline().fit(x_train) if champion_name == "baseline_zscore" else IsolationForestModel().fit(x_train)
            scores = model.score(x_test)
            threshold = float(np.percentile(scores, 99))

            if champion_name == "baseline_zscore":
                contributions_list = [
                    baseline_feature_contribution(x_test[i], model.median_, model.mad_, feature_names)
                    for i in range(len(x_test))
                ]
            else:
                contributions_list = [{} for _ in range(len(x_test))]

        champion_model_version_id = champion_mv.id

        # health_index normalizado pelo limiar (Seção 11 do blueprint: "a
        # normalização deve ser calibrada na validação e documentada"), não
        # pelo máximo do split de teste — normalizar pelo máximo comprimia
        # scores já acima do limiar para perto de 100 (verde) sempre que
        # existisse um outlier bem maior em outro ponto do teste, mostrando
        # "Alerta" ao lado de um índice de saúde alto. Score == limiar ⇒
        # health_index = 50; score >= 2×limiar ⇒ health_index = 0 (mesma
        # escala usada para decidir o estado normal/attention/alert abaixo).
        health_scale = 2 * threshold if threshold > 0 else 1.0

        prediction_runs: list[PredictionRun] = []
        alerts: list[Alert] = []
        for start, end, score, contributions in zip(window_starts, window_ends, scores, contributions_list):
            health_index = 100 * max(0.0, min(1.0, 1 - float(score) / health_scale))
            state = "alert" if score >= threshold else ("attention" if score >= 0.7 * threshold else "normal")
            pr_id = uuid.uuid4()
            prediction_runs.append(
                PredictionRun(
                    id=pr_id,
                    model_version_id=champion_model_version_id,
                    window_start=start,
                    window_end=end,
                    anomaly_score=float(score),
                    health_index=health_index,
                    state=state,
                    feature_contributions=contributions,
                )
            )
            if state == "alert":
                alerts.append(
                    Alert(
                        prediction_run_id=pr_id,
                        severity="alert",
                        reason=(
                            "Score de anomalia acima do limiar calibrado na validação. "
                            "Rótulo-proxy — ver docs/formulacao-do-problema.md."
                        ),
                    )
                )

        # Insere em lotes pequenos, com commit a cada lote: uma única
        # transação gigante sobre o proxy TCP do Railway se mostrou instável
        # (conexão derrubada a meio caminho). IDs gerados em Python (acima)
        # permitem popular prediction_run_id dos alertas sem depender de
        # round-trip de flush por linha.
        BATCH_SIZE = 200
        for i in range(0, len(prediction_runs), BATCH_SIZE):
            db.bulk_save_objects(prediction_runs[i : i + BATCH_SIZE])
            db.commit()
        for i in range(0, len(alerts), BATCH_SIZE):
            db.bulk_save_objects(alerts[i : i + BATCH_SIZE])
            db.commit()

        print(f"Modelo campeão marcado como ativo: {champion_name}")
        print(f"{len(prediction_runs)} previsões e {len(alerts)} alertas de demonstração inseridos")


if __name__ == "__main__":
    main()
