from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload

from app.api.common import parse_uuid
from app.db.models import EvaluationRun
from app.db.session import get_db

router = APIRouter(prefix="/api/evaluations", tags=["evaluations"])


def _serialize(e: EvaluationRun) -> dict:
    return {
        "id": str(e.id),
        "model_version_id": str(e.model_version_id),
        "model_name": e.model_version.name,
        "configuration": e.configuration,
        "metrics": e.metrics,
        "confusion_matrix": e.confusion_matrix,
        "started_at": e.started_at,
        "finished_at": e.finished_at,
    }


@router.get("")
def list_evaluations(db: Session = Depends(get_db)) -> list[dict]:
    runs = (
        db.query(EvaluationRun)
        .options(joinedload(EvaluationRun.model_version))
        .order_by(EvaluationRun.started_at.desc())
        .all()
    )
    return [_serialize(e) for e in runs]


@router.get("/{evaluation_id}")
def get_evaluation(evaluation_id: str, db: Session = Depends(get_db)) -> dict:
    run = (
        db.query(EvaluationRun)
        .options(joinedload(EvaluationRun.model_version))
        .filter(EvaluationRun.id == parse_uuid(evaluation_id))
        .first()
    )
    if run is None:
        raise HTTPException(status_code=404, detail="Avaliação não encontrada")
    return _serialize(run)


@router.post("/run")
def trigger_evaluation_run() -> dict:
    # Seção 13 do blueprint: treino/avaliação pesada roda por script, não
    # por endpoint público no MVP. Este endpoint existe só para não quebrar
    # o contrato da API — devolve instrução, não executa nada.
    raise HTTPException(
        status_code=501,
        detail=(
            "Avaliação não é executada via API no MVP. Rode "
            "'backend\\scripts\\run_decision_matrix.py' e depois "
            "'backend\\scripts\\populate_db.py'."
        ),
    )
