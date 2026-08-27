"""Tratamento de NaN/inf nos atributos derivados antes da modelagem.

Skewness e kurtose (scipy.stats) ficam indefinidas quando a janela é
praticamente constante (variância ~0) — o que acontece nos blocos de
baixa atividade de `Oct.csv` (ver relatório de qualidade). Nesses casos
não há "forma" de distribuição a descrever; substituir por 0.0 é uma
decisão explícita de neutralidade, documentada aqui, não uma imputação
silenciosa.
"""

import numpy as np


def sanitize_features(features: np.ndarray) -> np.ndarray:
    return np.nan_to_num(features, nan=0.0, posinf=0.0, neginf=0.0)
