from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.common import parse_uuid
from app.db.models import Dataset, IngestionRun
from app.db.session import get_db

router = APIRouter(prefix="/api/datasets", tags=["datasets"])


@router.get("")
def list_datasets(db: Session = Depends(get_db)) -> list[dict]:
    datasets = db.query(Dataset).order_by(Dataset.created_at.desc()).all()
    return [
        {
            "id": str(d.id),
            "name": d.name,
            "source_url": d.source_url,
            "license": d.license,
            "version": d.version,
            "time_start": d.time_start,
            "time_end": d.time_end,
            "metadata": d.dataset_metadata,
        }
        for d in datasets
    ]


@router.get("/{dataset_id}/quality")
def dataset_quality(dataset_id: str, db: Session = Depends(get_db)) -> dict:
    run = (
        db.query(IngestionRun)
        .filter(IngestionRun.dataset_id == parse_uuid(dataset_id))
        .order_by(IngestionRun.started_at.desc())
        .first()
    )
    if run is None:
        raise HTTPException(status_code=404, detail="Nenhuma execução de ingestão encontrada para este dataset")
    return {
        "status": run.status,
        "row_count": run.row_count,
        "pipeline_version": run.pipeline_version,
        "quality_report": run.quality_report,
    }


@router.get("/{dataset_id}/drift")
def dataset_drift(dataset_id: str, db: Session = Depends(get_db)) -> dict:
    """Extensão pós-MVP (Seção 20 do blueprint): drift de dados por período,
    calculado por `backend/scripts/run_drift_report.py`. Ausente para
    datasets populados antes dessa extensão."""
    dataset = db.query(Dataset).filter(Dataset.id == parse_uuid(dataset_id)).first()
    if dataset is None:
        raise HTTPException(status_code=404, detail="Dataset não encontrado")
    report = dataset.dataset_metadata.get("drift_report")
    if report is None:
        raise HTTPException(status_code=404, detail="Relatório de drift não disponível para este dataset")
    return report
