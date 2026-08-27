"""Atributos derivados por janela — feature_set_v1.

Começa deliberadamente pequeno (Seção 8.3 do blueprint): estatísticas
descritivas básicas por canal e por janela. Cada grupo adicional de
atributos deve ser comparado ao baseline via ablação antes de ser
incorporado — não faz parte do MVP do Marco 2 produzir dezenas de
atributos sem essa comparação.
"""

import numpy as np
from scipy import stats

FEATURE_SET_VERSION = "v1"


def compute_window_features(values: np.ndarray, feature_columns: list[str]) -> tuple[np.ndarray, list[str]]:
    """values: (n_windows, window_size, n_features) -> (n_windows, n_derived), nomes."""
    n_windows, window_size, n_features = values.shape

    mean = values.mean(axis=1)
    std = values.std(axis=1)
    rms = np.sqrt((values**2).mean(axis=1))
    peak_to_peak = values.max(axis=1) - values.min(axis=1)
    skewness = stats.skew(values, axis=1, bias=False, nan_policy="propagate")
    kurtosis = stats.kurtosis(values, axis=1, bias=False, nan_policy="propagate")

    derived = np.concatenate([mean, std, rms, peak_to_peak, skewness, kurtosis], axis=1)

    names: list[str] = []
    for stat_name in ("mean", "std", "rms", "peak_to_peak", "skewness", "kurtosis"):
        names.extend(f"{col}__{stat_name}" for col in feature_columns)

    return derived, names
