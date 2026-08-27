"""Auditoria exploratória dos arquivos brutos em data/raw/.

Não faz parte do pipeline de produção. Uso único para produzir os
documentos do Marco 1 (dicionário de dados, relatório de qualidade,
formulação do problema). Resultado impresso em stdout.
"""

from pathlib import Path

import pandas as pd

RAW_DIR = Path(__file__).resolve().parents[2] / "data" / "raw"


def audit_file(path: Path) -> None:
    df = pd.read_csv(path)
    df.columns = [c.strip() for c in df.columns]
    unnamed = [c for c in df.columns if c.startswith("Unnamed")]

    ts_col = df.columns[0]
    ts = pd.to_datetime(df[ts_col], format="%Y/%m/%d %H:%M:%S", errors="coerce")

    print(f"\n=== {path.name} ===")
    print(f"linhas: {len(df)} | colunas: {len(df.columns)} | colunas vazias (Unnamed): {len(unnamed)}")
    print(f"timestamps não parseáveis: {ts.isna().sum()}")
    print(f"intervalo: {ts.min()} -> {ts.max()}")
    print(f"duplicados de timestamp: {ts.duplicated().sum()}")
    diffs = ts.sort_values().diff().dropna()
    if not diffs.empty:
        print(f"passo mediano: {diffs.median()} | passo mínimo: {diffs.min()} | passo máximo: {diffs.max()}")
    is_monotonic = ts.is_monotonic_increasing
    print(f"ordenado no arquivo original: {is_monotonic}")

    value_cols = [c for c in df.columns if c not in (ts_col,) and not c.startswith("Unnamed")]
    print(f"colunas de valor ({len(value_cols)}):")
    for c in value_cols:
        s = pd.to_numeric(df[c], errors="coerce")
        n_na = s.isna().sum()
        n_zero = (s == 0).sum()
        print(
            f"  - {c!r}: min={s.min():.4f} max={s.max():.4f} mean={s.mean():.4f} "
            f"NA={n_na} zeros={n_zero} ({100*n_zero/len(s):.1f}%)"
        )


def main() -> None:
    files = sorted(RAW_DIR.glob("*.csv"))
    print(f"Arquivos encontrados: {[f.name for f in files]}")
    for f in files:
        audit_file(f)


if __name__ == "__main__":
    main()
