"""Janelamento temporal sem vazamento entre arquivos ou splits.

Regra central (Seção 8.2 do blueprint): janelas sobrepostas não podem
atravessar fronteiras entre treino, validação e teste. Como cada arquivo
mensal já pertence integralmente a um único split (ver `splits.py`) e há
uma lacuna real de dados entre o fim de um mês e o início do próximo
(dias 29-31 ausentes — ver relatório de qualidade), a implementação
mais simples e a mais segura é a mesma: **nunca gerar uma janela que
misture linhas de mais de um `source_file`.** Isso torna o cruzamento de
split geometricamente impossível, não apenas evitado por sorte.
"""

from dataclasses import dataclass

import numpy as np
import pandas as pd


@dataclass
class WindowSet:
    values: np.ndarray  # shape (n_windows, window_size, n_features)
    window_start: list[pd.Timestamp]
    window_end: list[pd.Timestamp]
    source_file: list[str]
    split: list[str]


def make_windows(
    df: pd.DataFrame,
    feature_columns: list[str],
    window_size: int,
    stride: int,
) -> WindowSet:
    if window_size <= 0 or stride <= 0:
        raise ValueError("window_size e stride devem ser positivos")

    values_list = []
    starts, ends, sources, splits = [], [], [], []

    for source_file, group in df.groupby("source_file", sort=False):
        group = group.sort_values("timestamp")
        arr = group[feature_columns].to_numpy(dtype=float)
        ts = group["timestamp"].to_numpy()
        split_name = group["split"].iloc[0]

        n = len(group)
        for start_idx in range(0, n - window_size + 1, stride):
            end_idx = start_idx + window_size
            values_list.append(arr[start_idx:end_idx])
            starts.append(ts[start_idx])
            ends.append(ts[end_idx - 1])
            sources.append(source_file)
            splits.append(split_name)

    values = np.stack(values_list) if values_list else np.empty((0, window_size, len(feature_columns)))
    return WindowSet(
        values=values,
        window_start=starts,
        window_end=ends,
        source_file=sources,
        split=splits,
    )
