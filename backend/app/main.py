import logging

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.alerts import router as alerts_router
from app.api.datasets import router as datasets_router
from app.api.evaluations import router as evaluations_router
from app.api.health import router as health_router
from app.api.models import router as models_router
from app.api.monitoring import router as monitoring_router
from app.api.signals import router as signals_router
from app.core.config import get_settings

settings = get_settings()

app = FastAPI(
    title="Hydro Bearing Predictive Maintenance API",
    description=(
        "API de apoio à decisão para monitoramento de condição de mancal-guia "
        "de turbina hidráulica. Não emite comandos para equipamentos."
    ),
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health_router)
app.include_router(datasets_router)
app.include_router(signals_router)
app.include_router(models_router)
app.include_router(monitoring_router)
app.include_router(alerts_router)
app.include_router(evaluations_router)

logger = logging.getLogger("app")


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    # Seção 17 do blueprint: nunca expor stack traces na interface.
    logger.exception("Erro não tratado em %s", request.url.path)
    return JSONResponse(status_code=500, content={"detail": "Erro interno do servidor"})
