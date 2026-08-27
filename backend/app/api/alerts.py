from datetime import datetime, timezone

from fastapi import APIRouter, Body, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload

from app.api.common import parse_uuid
from app.db.models import Alert, PredictionRun
from app.db.session import get_db

router = APIRouter(prefix="/api/alerts", tags=["alerts"])


def _serialize(a: Alert) -> dict:
    return {
        "id": str(a.id),
        "prediction_run_id": str(a.prediction_run_id),
        "severity": a.severity,
        "reason": a.reason,
        "acknowledged": a.acknowledged,
        "acknowledged_at": a.acknowledged_at,
        "notes": a.notes,
        "window_start": a.prediction_run.window_start,
        "window_end": a.prediction_run.window_end,
    }


@router.get("")
def list_alerts(acknowledged: bool | None = None, limit: int = 100, db: Session = Depends(get_db)) -> list[dict]:
    limit = min(limit, 500)
    query = db.query(Alert).options(joinedload(Alert.prediction_run)).join(PredictionRun)
    if acknowledged is not None:
        query = query.filter(Alert.acknowledged == acknowledged)
    alerts = query.order_by(PredictionRun.window_end.desc()).limit(limit).all()
    return [_serialize(a) for a in alerts]


@router.patch("/{alert_id}")
def update_alert(alert_id: str, payload: dict = Body(...), db: Session = Depends(get_db)) -> dict:
    alert = db.query(Alert).filter(Alert.id == parse_uuid(alert_id)).first()
    if alert is None:
        raise HTTPException(status_code=404, detail="Alerta não encontrado")

    if "acknowledged" in payload:
        alert.acknowledged = bool(payload["acknowledged"])
        alert.acknowledged_at = datetime.now(timezone.utc) if alert.acknowledged else None
    if "notes" in payload:
        alert.notes = str(payload["notes"])[:2000]

    db.commit()
    db.refresh(alert)
    return _serialize(alert)
