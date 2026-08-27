from datetime import datetime

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.db.models import ModelVersion, PredictionRun
from app.db.session import get_db

router = APIRouter(prefix="/api/monitoring", tags=["monitoring"])


@router.get("/current")
def current_state(db: Session = Depends(get_db)) -> dict:
    active_model = db.query(ModelVersion).filter(ModelVersion.status == "active").first()
    if active_model is None:
        return {"state": "model_unavailable", "message": "Nenhum modelo ativo configurado"}

    latest = (
        db.query(PredictionRun)
        .filter(PredictionRun.model_version_id == active_model.id)
        .order_by(PredictionRun.window_end.desc())
        .first()
    )
    if latest is None:
        return {"state": "insufficient_data", "model": active_model.name}

    return {
        "state": latest.state,
        "health_index": latest.health_index,
        "anomaly_score": latest.anomaly_score,
        "threshold": active_model.hyperparameters.get("threshold"),
        "window_start": latest.window_start,
        "window_end": latest.window_end,
        "model_name": active_model.name,
        "model_id": str(active_model.id),
        "feature_contributions": latest.feature_contributions,
    }


@router.get("/timeline")
def timeline(
    start: datetime | None = Query(None),
    end: datetime | None = Query(None),
    db: Session = Depends(get_db),
) -> dict:
    active_model = db.query(ModelVersion).filter(ModelVersion.status == "active").first()
    if active_model is None:
        return {"state": "model_unavailable", "points": []}

    query = db.query(PredictionRun).filter(PredictionRun.model_version_id == active_model.id)
    if start is not None:
        query = query.filter(PredictionRun.window_end >= start)
    if end is not None:
        query = query.filter(PredictionRun.window_end <= end)

    # Sem start/end, ordenar decrescente e limitar evita devolver o histórico inteiro.
    order = PredictionRun.window_end if start is not None else PredictionRun.window_end.desc()
    rows = query.order_by(order).limit(5000).all()
    if start is None:
        rows = list(reversed(rows))
    return {
        "model_name": active_model.name,
        "threshold": active_model.hyperparameters.get("threshold"),
        "points": [
            {
                "window_start": r.window_start,
                "window_end": r.window_end,
                "anomaly_score": r.anomaly_score,
                "health_index": r.health_index,
                "state": r.state,
                "feature_contributions": r.feature_contributions,
            }
            for r in rows
        ],
    }
