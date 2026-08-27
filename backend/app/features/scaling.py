"""Ajuste de scaler exclusivamente no treino (Seção 8.2 do blueprint).

Nunca chamar `fit` ou `fit_transform` com dados de validação ou teste.
`fit_scaler` só aceita a matriz de atributos já filtrada para o split de
treino, para tornar o erro impossível de cometer por engano de código.
"""

import joblib
import numpy as np
from sklearn.preprocessing import StandardScaler


def fit_scaler(train_features: np.ndarray) -> StandardScaler:
    scaler = StandardScaler()
    scaler.fit(train_features)
    return scaler


def save_scaler(scaler: StandardScaler, path) -> None:
    joblib.dump(scaler, path)


def load_scaler(path) -> StandardScaler:
    return joblib.load(path)
