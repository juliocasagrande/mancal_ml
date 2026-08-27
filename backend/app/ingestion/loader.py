"""Carregamento e limpeza de um arquivo bruto mensal da unidade G1.

Regras aplicadas (ver docs/relatorio-qualidade-dataset.md):
- o arquivo original nunca é modificado, apenas lido;
- a 14ª coluna (vazia, gerada por vírgula final no cabeçalho) é descartada;
- timestamps são parseados no formato `%Y/%m/%d %H:%M:%S`; linhas cujo
  timestamp não parseia são removidas (não podem ser posicionadas na
  série) e contadas no relatório de qualidade, não silenciosamente;
- linhas duplicadas de timestamp mantêm a primeira ocorrência;
- linhas são ordenadas por tempo;
- valores numéricos ausentes NÃO são imputados aqui — ficam como NaN e são
  sinalizados na coluna `has_missing`. Imputação é decisão de modelagem,
  feita depois do split (Marco 2/3), nunca antes.
"""

from dataclasses import dataclass, field
from pathlib import Path

import pandas as pd

from app.ingestion.schema import RAW_COLUMNS_G1, VALUE_COLUMNS


@dataclass
class LoadReport:
    source_file: str
    rows_raw: int
    rows_after_clean: int
    rows_dropped_bad_timestamp: int
    rows_dropped_duplicate_timestamp: int
    time_start: pd.Timestamp | None
    time_end: pd.Timestamp | None
    nominal_freq_minutes: int
    observed_freq_minutes: float | None
    rows_with_missing: int
    notes: list[str] = field(default_factory=list)


def load_raw_g1_file(path: Path, nominal_freq_minutes: int = 10) -> tuple[pd.DataFrame, LoadReport]:
    raw = pd.read_csv(path, header=0)
    rows_raw = len(raw)

    # A 14ª coluna é o "Unnamed" residual da vírgula final do cabeçalho.
    raw = raw.iloc[:, : len(RAW_COLUMNS_G1)]
    raw.columns = RAW_COLUMNS_G1

    ts = pd.to_datetime(raw["timestamp"], format="%Y/%m/%d %H:%M:%S", errors="coerce")
    n_bad_ts = int(ts.isna().sum())
    df = raw.assign(timestamp=ts).dropna(subset=["timestamp"])

    n_before_dedup = len(df)
    df = df.drop_duplicates(subset="timestamp", keep="first")
    n_dropped_dup = n_before_dedup - len(df)

    df = df.sort_values("timestamp").reset_index(drop=True)

    for col in VALUE_COLUMNS:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    df["has_missing"] = df[VALUE_COLUMNS].isna().any(axis=1)
    df["source_file"] = path.name

    observed_freq = None
    if len(df) > 1:
        deltas = df["timestamp"].diff().dropna().dt.total_seconds() / 60
        observed_freq = float(deltas.median())

    report = LoadReport(
        source_file=path.name,
        rows_raw=rows_raw,
        rows_after_clean=len(df),
        rows_dropped_bad_timestamp=n_bad_ts,
        rows_dropped_duplicate_timestamp=n_dropped_dup,
        time_start=df["timestamp"].min() if len(df) else None,
        time_end=df["timestamp"].max() if len(df) else None,
        nominal_freq_minutes=nominal_freq_minutes,
        observed_freq_minutes=observed_freq,
        rows_with_missing=int(df["has_missing"].sum()),
    )
    if observed_freq is not None and observed_freq != nominal_freq_minutes:
        report.notes.append(
            f"frequência observada ({observed_freq} min) difere da nominal ({nominal_freq_minutes} min)"
        )

    return df, report
