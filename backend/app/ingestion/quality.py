"""Consolidação do relatório de qualidade da execução de ingestão.

Implementa o contrato descrito na Seção 8.1 do blueprint: toda execução
registra dataset_version, hash, intervalo, contagem de linhas, colunas,
frequência nominal/observada, dados ausentes/duplicados/fora de ordem,
regras aplicadas e versão do código.
"""

import json
import subprocess
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path

from app.ingestion.loader import LoadReport


def _git_commit() -> str | None:
    try:
        out = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            capture_output=True,
            text=True,
            check=True,
            cwd=Path(__file__).resolve().parents[3],
        )
        return out.stdout.strip()
    except Exception:
        return None


def build_ingestion_run_report(
    dataset_version: str,
    manifest_path: Path,
    file_reports: list[LoadReport],
    pipeline_version: str,
) -> dict:
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    hashes = {f["local_name"]: f["sha256"] for f in manifest["files"]}

    total_rows = sum(r.rows_after_clean for r in file_reports)
    time_start = min((r.time_start for r in file_reports if r.time_start is not None), default=None)
    time_end = max((r.time_end for r in file_reports if r.time_end is not None), default=None)

    return {
        "dataset_version": dataset_version,
        "pipeline_version": pipeline_version,
        "git_commit": _git_commit(),
        "run_started_at": datetime.now(timezone.utc).isoformat(),
        "row_count": total_rows,
        "time_start": str(time_start) if time_start is not None else None,
        "time_end": str(time_end) if time_end is not None else None,
        "files": [
            {
                **asdict(r),
                "time_start": str(r.time_start) if r.time_start is not None else None,
                "time_end": str(r.time_end) if r.time_end is not None else None,
                "sha256": hashes.get(r.source_file),
            }
            for r in file_reports
        ],
        "rules_applied": [
            "arquivos originais tratados como somente leitura",
            "coluna vazia (14ª) descartada",
            "timestamps não parseáveis removidos e contados",
            "duplicados de timestamp removidos mantendo a primeira ocorrência",
            "linhas ordenadas por tempo",
            "valores ausentes marcados em 'has_missing', não imputados na ingestão",
        ],
    }


def save_report(report: dict, out_path: Path) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
