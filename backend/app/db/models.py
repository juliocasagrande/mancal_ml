"""Modelo de dados no Railway PostgreSQL — Seção 12 do blueprint.

Decisão de escopo: o dataset G1 tem ~24 mil amostras (pequeno o
suficiente para justificar persistir cada amostra, ao contrário do que a
Seção 12 previne para volumes maiores). `signal_samples` guarda o sinal
limpo (saída de `build_dataset.py`), não o arquivo bruto.
"""

import uuid
from datetime import datetime, timezone

from sqlalchemy import JSON, Boolean, DateTime, Float, ForeignKey, Integer, String, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _uuid_pk() -> Mapped[uuid.UUID]:
    return mapped_column(Uuid(), primary_key=True, default=uuid.uuid4)


class Dataset(Base):
    __tablename__ = "datasets"

    id: Mapped[uuid.UUID] = _uuid_pk()
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    source_url: Mapped[str] = mapped_column(Text, nullable=False)
    license: Mapped[str] = mapped_column(String(64), nullable=False)
    version: Mapped[str] = mapped_column(String(64), nullable=False)
    sha256: Mapped[str] = mapped_column(String(64), nullable=True)
    time_start: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    time_end: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    dataset_metadata: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)

    ingestion_runs: Mapped[list["IngestionRun"]] = relationship(back_populates="dataset")


class IngestionRun(Base):
    __tablename__ = "ingestion_runs"

    id: Mapped[uuid.UUID] = _uuid_pk()
    dataset_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("datasets.id"), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    row_count: Mapped[int] = mapped_column(Integer, nullable=True)
    quality_report: Mapped[dict] = mapped_column(JSON, default=dict)
    pipeline_version: Mapped[str] = mapped_column(String(64), nullable=False)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    finished_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    error_message: Mapped[str] = mapped_column(Text, nullable=True)

    dataset: Mapped[Dataset] = relationship(back_populates="ingestion_runs")


class SignalSample(Base):
    """Sinal limpo da unidade G1 (saída de build_dataset.py), não o bruto."""

    __tablename__ = "signal_samples"

    id: Mapped[uuid.UUID] = _uuid_pk()
    dataset_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("datasets.id"), nullable=False)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    source_file: Mapped[str] = mapped_column(String(64), nullable=False)
    split: Mapped[str] = mapped_column(String(16), nullable=False)

    generator_power: Mapped[float] = mapped_column(Float, nullable=True)
    unit_speed_pct: Mapped[float] = mapped_column(Float, nullable=True)
    temp_thrust_pad1: Mapped[float] = mapped_column(Float, nullable=True)
    temp_upper_guide_pad1: Mapped[float] = mapped_column(Float, nullable=True)
    temp_lower_guide_pad1: Mapped[float] = mapped_column(Float, nullable=True)
    temp_turbine_guide_pad1: Mapped[float] = mapped_column(Float, nullable=True)
    vib_ugb_x: Mapped[float] = mapped_column(Float, nullable=True)
    vib_ugb_y: Mapped[float] = mapped_column(Float, nullable=True)
    vib_ugb_z: Mapped[float] = mapped_column(Float, nullable=True)
    vib_lgb_x: Mapped[float] = mapped_column(Float, nullable=True)
    vib_lgb_y: Mapped[float] = mapped_column(Float, nullable=True)
    vib_tgb_x: Mapped[float] = mapped_column(Float, nullable=True)

    quality_flags: Mapped[dict] = mapped_column(JSON, default=dict)


class ModelVersion(Base):
    __tablename__ = "model_versions"

    id: Mapped[uuid.UUID] = _uuid_pk()
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    algorithm: Mapped[str] = mapped_column(String(64), nullable=False)
    artifact_path: Mapped[str] = mapped_column(Text, nullable=False)
    dataset_version: Mapped[str] = mapped_column(String(64), nullable=False)
    feature_schema: Mapped[dict] = mapped_column(JSON, default=dict)
    hyperparameters: Mapped[dict] = mapped_column(JSON, default=dict)
    metrics: Mapped[dict] = mapped_column(JSON, default=dict)
    status: Mapped[str] = mapped_column(String(32), default="candidate")  # candidate | active | archived
    git_commit: Mapped[str] = mapped_column(String(40), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)

    prediction_runs: Mapped[list["PredictionRun"]] = relationship(back_populates="model_version")
    evaluation_runs: Mapped[list["EvaluationRun"]] = relationship(back_populates="model_version")


class PredictionRun(Base):
    __tablename__ = "prediction_runs"

    id: Mapped[uuid.UUID] = _uuid_pk()
    model_version_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("model_versions.id"), nullable=False)
    window_start: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    window_end: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    anomaly_score: Mapped[float] = mapped_column(Float, nullable=False)
    health_index: Mapped[float] = mapped_column(Float, nullable=False)
    state: Mapped[str] = mapped_column(String(32), nullable=False)
    feature_contributions: Mapped[dict] = mapped_column(JSON, default=dict)
    latency_ms: Mapped[float] = mapped_column(Float, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)

    model_version: Mapped[ModelVersion] = relationship(back_populates="prediction_runs")
    alerts: Mapped[list["Alert"]] = relationship(back_populates="prediction_run")


class Alert(Base):
    __tablename__ = "alerts"

    id: Mapped[uuid.UUID] = _uuid_pk()
    prediction_run_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("prediction_runs.id"), nullable=False)
    severity: Mapped[str] = mapped_column(String(16), nullable=False)  # attention | alert
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    acknowledged: Mapped[bool] = mapped_column(Boolean, default=False)
    acknowledged_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    notes: Mapped[str] = mapped_column(Text, nullable=True)

    prediction_run: Mapped[PredictionRun] = relationship(back_populates="alerts")


class EvaluationRun(Base):
    __tablename__ = "evaluation_runs"

    id: Mapped[uuid.UUID] = _uuid_pk()
    model_version_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("model_versions.id"), nullable=False)
    configuration: Mapped[dict] = mapped_column(JSON, default=dict)
    metrics: Mapped[dict] = mapped_column(JSON, default=dict)
    confusion_matrix: Mapped[dict] = mapped_column(JSON, default=dict)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    finished_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)

    model_version: Mapped[ModelVersion] = relationship(back_populates="evaluation_runs")
