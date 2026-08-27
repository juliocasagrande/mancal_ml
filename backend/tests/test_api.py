"""Testes da API sobre um SQLite em memória (não requer o Postgres do
Railway) — a Uuid() do SQLAlchemy 2.0 é portátil entre dialetos, então o
mesmo modelo funciona nos dois bancos sem migração paralela.
"""

from datetime import datetime, timedelta

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.base import Base
from app.db.models import Alert, Dataset, ModelVersion, PredictionRun
from app.db.session import get_db
from app.main import app


@pytest.fixture()
def db_session():
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)
    session_factory = sessionmaker(bind=engine)
    session = session_factory()
    yield session
    session.close()


@pytest.fixture()
def client(db_session):
    def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    yield TestClient(app)
    app.dependency_overrides.clear()


def _seed_model_and_prediction(db_session, state="normal"):
    model = ModelVersion(
        name="lstm_autoencoder",
        algorithm="lstm_autoencoder",
        artifact_path="artifacts/lstm_autoencoder_v1",
        dataset_version="test-v1",
        status="active",
    )
    db_session.add(model)
    db_session.flush()

    prediction = PredictionRun(
        model_version_id=model.id,
        window_start=datetime(2020, 11, 1),
        window_end=datetime(2020, 11, 1, 6),
        anomaly_score=1.0,
        health_index=90.0,
        state=state,
    )
    db_session.add(prediction)
    db_session.flush()
    db_session.commit()
    return model, prediction


def test_health_endpoint(client) -> None:
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_datasets_empty_list(client) -> None:
    response = client.get("/api/datasets")
    assert response.status_code == 200
    assert response.json() == []


def test_dataset_quality_404_for_unknown_dataset(client) -> None:
    response = client.get("/api/datasets/11111111-1111-1111-1111-111111111111/quality")
    assert response.status_code == 404


def test_invalid_uuid_returns_422_not_500(client) -> None:
    response = client.get("/api/models/not-a-valid-uuid")
    assert response.status_code == 422


def test_monitoring_current_reports_model_unavailable_when_no_active_model(client) -> None:
    response = client.get("/api/monitoring/current")
    assert response.status_code == 200
    assert response.json()["state"] == "model_unavailable"


def test_monitoring_current_reports_insufficient_data_without_predictions(client, db_session) -> None:
    db_session.add(
        ModelVersion(
            name="m", algorithm="m", artifact_path="x", dataset_version="v1", status="active"
        )
    )
    db_session.commit()

    response = client.get("/api/monitoring/current")
    assert response.status_code == 200
    assert response.json()["state"] == "insufficient_data"


def test_monitoring_current_returns_latest_prediction(client, db_session) -> None:
    _seed_model_and_prediction(db_session, state="alert")

    response = client.get("/api/monitoring/current")
    body = response.json()
    assert body["state"] == "alert"
    assert body["health_index"] == 90.0


def test_models_list_and_get(client, db_session) -> None:
    model, _ = _seed_model_and_prediction(db_session)

    listed = client.get("/api/models").json()
    assert len(listed) == 1

    fetched = client.get(f"/api/models/{model.id}")
    assert fetched.status_code == 200
    assert fetched.json()["name"] == "lstm_autoencoder"


def test_activate_model_archives_previous_active(client, db_session) -> None:
    active_model, _ = _seed_model_and_prediction(db_session)
    candidate = ModelVersion(
        name="baseline_zscore", algorithm="baseline_zscore", artifact_path="x", dataset_version="v1",
        status="candidate",
    )
    db_session.add(candidate)
    db_session.commit()

    response = client.post(f"/api/models/{candidate.id}/activate")
    assert response.status_code == 200
    assert response.json()["status"] == "active"

    db_session.refresh(active_model)
    assert active_model.status == "archived"


def test_alerts_list_and_acknowledge(client, db_session) -> None:
    _, prediction = _seed_model_and_prediction(db_session, state="alert")
    alert = Alert(prediction_run_id=prediction.id, severity="alert", reason="teste")
    db_session.add(alert)
    db_session.commit()

    listed = client.get("/api/alerts").json()
    assert len(listed) == 1
    assert listed[0]["acknowledged"] is False

    patched = client.patch(f"/api/alerts/{alert.id}", json={"acknowledged": True, "notes": "ok"})
    assert patched.status_code == 200
    assert patched.json()["acknowledged"] is True
    assert patched.json()["notes"] == "ok"


def test_alerts_404_for_unknown_alert(client) -> None:
    response = client.patch(
        "/api/alerts/11111111-1111-1111-1111-111111111111", json={"acknowledged": True}
    )
    assert response.status_code == 404


def test_signals_range_rejects_range_over_limit(client) -> None:
    start = datetime(2020, 1, 1)
    end = start + timedelta(days=200)
    response = client.get(
        "/api/signals/range",
        params={"start": start.isoformat(), "end": end.isoformat()},
    )
    assert response.status_code == 422


def test_signals_range_rejects_end_before_start(client) -> None:
    response = client.get(
        "/api/signals/range",
        params={"start": "2020-06-02T00:00:00", "end": "2020-06-01T00:00:00"},
    )
    assert response.status_code == 422


def test_evaluations_run_endpoint_is_not_implemented(client) -> None:
    response = client.post("/api/evaluations/run")
    assert response.status_code == 501
