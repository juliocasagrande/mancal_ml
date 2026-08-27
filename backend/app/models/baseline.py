"""Baseline estatístico: z-score robusto (mediana/MAD) por atributo.

Seção 9.1 do blueprint. O score de uma janela é o maior |z-score| entre os
atributos monitorados — uma única variável fora do envelope saudável já
basta para sinalizar a janela. Mediana e MAD são ajustados apenas no
treino, como qualquer outro transformador.
"""

import numpy as np

MAD_TO_STD = 1.4826  # fator que torna o MAD comparável ao desvio-padrão sob normalidade


class RobustZScoreBaseline:
    def __init__(self) -> None:
        self.median_: np.ndarray | None = None
        self.mad_: np.ndarray | None = None

    def fit(self, train_features: np.ndarray) -> "RobustZScoreBaseline":
        self.median_ = np.median(train_features, axis=0)
        mad = np.median(np.abs(train_features - self.median_), axis=0)
        # MAD ~0 (atributo praticamente constante no treino) tornaria o
        # z-score explosivo e dominaria o max espuriamente. Em vez de um
        # epsilon artificial, marcamos esses atributos como não
        # informativos (NaN) e os excluímos do score via nanmax.
        self.mad_ = np.where(mad > 0, mad * MAD_TO_STD, np.nan)
        return self

    def score(self, features: np.ndarray) -> np.ndarray:
        if self.median_ is None or self.mad_ is None:
            raise RuntimeError("baseline não ajustado — chame fit() antes de score()")
        z = np.abs((features - self.median_) / self.mad_)
        if np.all(np.isnan(self.mad_)):
            return np.zeros(len(features))
        return np.nanmax(z, axis=1)
