from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.db.models import SignalSample
from app.db.session import get_db
from app.ingestion.schema import VALUE_COLUMNS

router = APIRouter(prefix="/api/signals", tags=["signals"])

MAX_RANGE_DAYS = 45  # limite de consulta — Seção 17 do blueprint ("limitar tamanho e período das consultas")
MAX_ROWS_RETURNED = 5000


@router.get("/range")
def signal_range(
    start: datetime = Query(...),
    end: datetime = Query(...),
    downsample: int = Query(1, ge=1, le=1000, description="retorna 1 a cada N amostras"),
    db: Session = Depends(get_db),
) -> dict:
    if end <= start:
        raise HTTPException(status_code=422, detail="'end' deve ser posterior a 'start'")
    if end - start > timedelta(days=MAX_RANGE_DAYS):
        raise HTTPException(status_code=422, detail=f"intervalo máximo de consulta é {MAX_RANGE_DAYS} dias")

    query = (
        db.query(SignalSample)
        .filter(SignalSample.timestamp >= start, SignalSample.timestamp <= end)
        .order_by(SignalSample.timestamp)
        .limit(MAX_ROWS_RETURNED * downsample)
    )
    rows = query.all()
    sampled = rows[::downsample][:MAX_ROWS_RETURNED]

    return {
        "n_points": len(sampled),
        "downsample": downsample,
        "truncated": len(rows) == MAX_ROWS_RETURNED * downsample,
        "points": [
            {
                "timestamp": r.timestamp,
                "source_file": r.source_file,
                "split": r.split,
                "quality_flags": r.quality_flags,
                **{col: getattr(r, col) for col in VALUE_COLUMNS},
            }
            for r in sampled
        ],
    }


@router.get("/summary")
def signal_summary(db: Session = Depends(get_db)) -> dict:
    total = db.query(func.count(SignalSample.id)).scalar()
    time_range = db.query(func.min(SignalSample.timestamp), func.max(SignalSample.timestamp)).first()
    by_split = dict(db.query(SignalSample.split, func.count(SignalSample.id)).group_by(SignalSample.split).all())
    by_file = dict(
        db.query(SignalSample.source_file, func.count(SignalSample.id)).group_by(SignalSample.source_file).all()
    )
    return {
        "total_samples": total,
        "time_start": time_range[0] if time_range else None,
        "time_end": time_range[1] if time_range else None,
        "samples_by_split": by_split,
        "samples_by_source_file": by_file,
        "value_columns": VALUE_COLUMNS,
    }
