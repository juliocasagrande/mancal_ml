import sys

from fastapi import APIRouter

from app.core.config import get_settings

router = APIRouter()


@router.get("/api/health")
def health() -> dict:
    settings = get_settings()
    return {
        "status": "ok",
        "app_env": settings.app_env,
        "python_version": sys.version.split()[0],
    }
