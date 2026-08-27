"""Rótulo-proxy de anomalia — NÃO é um rótulo de falha confirmado.

Conforme `docs/formulacao-do-problema.md`, o dataset não tem coluna de
falha. Para poder calcular métricas por evento (Seção 10 do blueprint) é
necessário algum proxy. Usamos operação com potência muito abaixo do
normal como proxy de "período de operação atípica" — pode ser parada
programada, não necessariamente degradação do mancal. Todo relatório que
usar este rótulo deve repetir essa ressalva.
"""

import numpy as np

# Fração da potência mediana do treino abaixo da qual uma janela é
# marcada como proxy de operação atípica. Limiar arbitrário e revisável,
# não uma verdade de campo.
LOW_POWER_FRACTION = 0.2


def build_proxy_labels(power_mean_column: np.ndarray, train_median_power: float) -> np.ndarray:
    threshold = LOW_POWER_FRACTION * train_median_power
    return power_mean_column < threshold
