from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.common import parse_uuid
from app.db.models import ModelVersion
from app.db.session import get_db

router = APIRouter(prefix="/api/models", tags=["models"])


def _serialize(m: ModelVersion) -> dict:
    return {
        "id": str(m.id),
        "name": m.name,
        "algorithm": m.algorithm,
        "dataset_version": m.dataset_version,
        "feature_schema": m.feature_schema,
        "hyperparameters": m.hyperparameters,
        "metrics": m.metrics,
        "status": m.status,
        "git_commit": m.git_commit,
        "created_at": m.created_at,
    }


@router.get("")
def list_models(db: Session = Depends(get_db)) -> list[dict]:
    models = db.query(ModelVersion).order_by(ModelVersion.created_at.desc()).all()
    return [_serialize(m) for m in models]


@router.get("/{model_id}")
def get_model(model_id: str, db: Session = Depends(get_db)) -> dict:
    model = db.query(ModelVersion).filter(ModelVersion.id == parse_uuid(model_id)).first()
    if model is None:
        raise HTTPException(status_code=404, detail="Modelo não encontrado")
    return _serialize(model)


@router.post("/{model_id}/activate")
def activate_model(model_id: str, db: Session = Depends(get_db)) -> dict:
    """Marca um modelo como ativo. Não dispara re-treino nem re-inferência —
    apenas muda o status de qual modelo a API de monitoramento usaria por
    padrão numa versão futura. Treino é sempre feito por script (Seção 13)."""
    target = db.query(ModelVersion).filter(ModelVersion.id == parse_uuid(model_id)).first()
    if target is None:
        raise HTTPException(status_code=404, detail="Modelo não encontrado")

    db.query(ModelVersion).filter(ModelVersion.status == "active").update({"status": "archived"})
    target.status = "active"
    db.commit()
    db.refresh(target)
    return _serialize(target)
