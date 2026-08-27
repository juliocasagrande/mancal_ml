"""Contribuição por variável ao score de anomalia — Seção 11 do blueprint.

Cada modelo decompõe o score de forma diferente; a interface comum é
"nome do canal -> fração do score total atribuível a ele" (soma 1,0).
Usado pela Página 4 do frontend (Marco 7) e pela justificativa de
explicabilidade na matriz de decisão (Marco 5).
"""

import numpy as np


def lstm_feature_contribution(
    window: np.ndarray,
    reconstructed: np.ndarray,
    feature_names: list[str],
) -> dict[str, float]:
    """window, reconstructed: (window_size, n_features), já na escala do scaler de sinal."""
    per_channel_error = ((window - reconstructed) ** 2).mean(axis=0)
    total = per_channel_error.sum()
    if total == 0:
        share = np.zeros_like(per_channel_error)
    else:
        share = per_channel_error / total
    return dict(zip(feature_names, share.tolist(), strict=True))


def baseline_feature_contribution(
    window_features: np.ndarray,
    median: np.ndarray,
    mad: np.ndarray,
    feature_names: list[str],
) -> dict[str, float]:
    """window_features: vetor de atributos derivados de uma única janela."""
    z = np.abs((window_features - median) / mad)
    z = np.nan_to_num(z, nan=0.0)
    total = z.sum()
    share = z / total if total > 0 else np.zeros_like(z)
    return dict(zip(feature_names, share.tolist(), strict=True))
