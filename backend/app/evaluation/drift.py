"""Detecção de drift de dados (extensão pós-MVP — Seção 20 do blueprint).

Mede o quanto a distribuição dos atributos derivados de um período (ex.:
um mês do split de teste) se afastou da distribuição observada no treino,
usando Population Stability Index (PSI) por atributo — técnica padrão de
monitoramento de modelos em produção, independente de rótulo.

PSI compara, por atributo, a fração de amostras do período atual em cada
decil da distribuição de treino contra a fração esperada (10% por decil).
Limiares de severidade (`< 0.1` sem drift, `< 0.25` moderado, `>= 0.25`
significativo) são a convenção usual da literatura de risco de crédito e
monitoramento de ML — não foram recalibrados para este dataset e devem
ser lidos como heurística, não verdade absoluta.

Drift é uma propriedade da distribuição dos dados, não do modelo: não
substitui o score de anomalia por janela (`app/models/`), é um sinal
complementar para saber se o regime operacional mudou o suficiente para
o modelo treinado deixar de ser confiável.
"""

from dataclasses import dataclass

import numpy as np

PSI_MODERATE_THRESHOLD = 0.1
PSI_SIGNIFICANT_THRESHOLD = 0.25
_EPS = 1e-6


@dataclass
class FeatureDrift:
    feature: str
    psi: float
    severity: str  # "none" | "moderate" | "significant" | "constante_no_treino"


@dataclass
class DriftReport:
    reference_n: int
    current_n: int
    overall_psi: float
    severity: str
    per_feature: list[FeatureDrift]


def classify_psi(value: float) -> str:
    if value < PSI_MODERATE_THRESHOLD:
        return "none"
    if value < PSI_SIGNIFICANT_THRESHOLD:
        return "moderate"
    return "significant"


def _reference_bin_edges(reference: np.ndarray, n_bins: int) -> np.ndarray:
    edges = np.unique(np.quantile(reference, np.linspace(0, 1, n_bins + 1)))
    if len(edges) >= 2:
        edges[0] = -np.inf
        edges[-1] = np.inf
    return edges


def _psi(reference: np.ndarray, current: np.ndarray, edges: np.ndarray) -> float:
    ref_counts, _ = np.histogram(reference, bins=edges)
    cur_counts, _ = np.histogram(current, bins=edges)
    ref_pct = np.clip(ref_counts / max(ref_counts.sum(), 1), _EPS, None)
    cur_pct = np.clip(cur_counts / max(cur_counts.sum(), 1), _EPS, None)
    return float(np.sum((cur_pct - ref_pct) * np.log(cur_pct / ref_pct)))


def compute_drift_report(
    reference: np.ndarray,
    current: np.ndarray,
    feature_names: list[str],
    n_bins: int = 10,
) -> DriftReport:
    """`reference`/`current`: arrays (n_amostras, n_atributos), mesma ordem
    de colunas que `feature_names`. `reference` deve vir só do treino.
    """
    per_feature: list[FeatureDrift] = []
    for i, name in enumerate(feature_names):
        ref_col = reference[:, i]
        cur_col = current[:, i]
        edges = _reference_bin_edges(ref_col, n_bins)
        if len(edges) < 3:
            # Atributo praticamente constante no treino (ex.: canal morto) —
            # sem variação de referência não há decil para comparar; mesma
            # decisão de "não informativo" do baseline (app/models/baseline.py).
            per_feature.append(FeatureDrift(feature=name, psi=0.0, severity="constante_no_treino"))
            continue
        value = _psi(ref_col, cur_col, edges)
        per_feature.append(FeatureDrift(feature=name, psi=value, severity=classify_psi(value)))

    overall_psi = float(np.mean([f.psi for f in per_feature])) if per_feature else 0.0
    return DriftReport(
        reference_n=len(reference),
        current_n=len(current),
        overall_psi=overall_psi,
        severity=classify_psi(overall_psi),
        per_feature=per_feature,
    )
