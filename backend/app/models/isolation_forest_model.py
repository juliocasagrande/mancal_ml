"""Wrapper do Isolation Forest com interface fit/score consistente com o
baseline estatístico, para permitir comparação direta na avaliação.
"""

import numpy as np
from sklearn.ensemble import IsolationForest


class IsolationForestModel:
    def __init__(self, n_estimators: int = 200, random_state: int = 42) -> None:
        self.model = IsolationForest(
            n_estimators=n_estimators,
            random_state=random_state,
            contamination="auto",
        )
        self._fitted = False

    def fit(self, train_features: np.ndarray) -> "IsolationForestModel":
        self.model.fit(train_features)
        self._fitted = True
        return self

    def score(self, features: np.ndarray) -> np.ndarray:
        if not self._fitted:
            raise RuntimeError("modelo não ajustado — chame fit() antes de score()")
        # score_samples: quanto MAIOR, mais normal. Invertido para manter a
        # convenção "quanto maior, mais anômalo" usada em todo o projeto.
        return -self.model.score_samples(features)
