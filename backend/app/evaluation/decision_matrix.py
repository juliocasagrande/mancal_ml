"""Matriz de decisão ponderada para escolha do modelo campeão — Seção 9.4
do blueprint. Pesos e critérios qualitativos são hipóteses operacionais
explícitas, não constantes definitivas.
"""

import numpy as np

DEFAULT_WEIGHTS = {
    "event_recall": 0.30,
    "false_alarms_per_day": 0.25,  # menor é melhor
    "detection_delay_windows": 0.20,  # menor é melhor
    "robustness": 0.10,
    "explainability": 0.10,
    "latency_p95_ms": 0.05,  # menor é melhor
}

LOWER_IS_BETTER = {"false_alarms_per_day", "detection_delay_windows", "latency_p95_ms"}


def _normalize(values: dict[str, float], lower_is_better: bool) -> dict[str, float]:
    arr = np.array(list(values.values()), dtype=float)
    if np.allclose(arr.max(), arr.min()):
        # todos os modelos empatam neste critério — não deve distorcer o ranking
        return {k: 1.0 for k in values}

    normalized = (arr - arr.min()) / (arr.max() - arr.min())
    if lower_is_better:
        normalized = 1.0 - normalized
    return dict(zip(values.keys(), normalized.tolist(), strict=True))


def compute_decision_matrix(
    criteria: dict[str, dict[str, float]],
    weights: dict[str, float] = DEFAULT_WEIGHTS,
) -> dict[str, dict]:
    """criteria: {modelo: {criterio: valor_bruto}}. Retorna score ponderado
    e a decomposição normalizada por critério, para transparência total.
    """
    models = list(criteria.keys())
    normalized_by_criterion = {}
    for criterion in weights:
        raw = {m: criteria[m][criterion] for m in models}
        normalized_by_criterion[criterion] = _normalize(raw, criterion in LOWER_IS_BETTER)

    scores = {}
    breakdown = {}
    for m in models:
        contributions = {c: normalized_by_criterion[c][m] * w for c, w in weights.items()}
        scores[m] = sum(contributions.values())
        breakdown[m] = {
            "weighted_score": scores[m],
            "normalized_criteria": {c: normalized_by_criterion[c][m] for c in weights},
            "raw_criteria": criteria[m],
        }
    return breakdown
