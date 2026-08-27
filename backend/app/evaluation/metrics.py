"""Métricas por janela e por evento (Seção 10 do blueprint)."""

from dataclasses import dataclass

import numpy as np
from sklearn.metrics import (
    average_precision_score,
    confusion_matrix,
    f1_score,
    precision_recall_curve,
    precision_score,
    recall_score,
    roc_auc_score,
)


@dataclass
class WindowMetrics:
    precision: float
    recall: float
    f1: float
    pr_auc: float
    roc_auc: float
    confusion_matrix: list[list[int]]


def compute_window_metrics(scores: np.ndarray, labels: np.ndarray, threshold: float) -> WindowMetrics:
    predictions = scores >= threshold
    labels = labels.astype(bool)

    if labels.sum() == 0 or labels.sum() == len(labels):
        # PR-AUC/ROC-AUC não são bem definidas com uma única classe presente.
        pr_auc = float("nan")
        roc_auc = float("nan")
    else:
        pr_auc = float(average_precision_score(labels, scores))
        roc_auc = float(roc_auc_score(labels, scores))

    return WindowMetrics(
        precision=float(precision_score(labels, predictions, zero_division=0)),
        recall=float(recall_score(labels, predictions, zero_division=0)),
        f1=float(f1_score(labels, predictions, zero_division=0)),
        pr_auc=pr_auc,
        roc_auc=roc_auc,
        confusion_matrix=confusion_matrix(labels, predictions, labels=[False, True]).tolist(),
    )


def compute_score_curves(scores: np.ndarray, labels: np.ndarray, n_bins: int = 25) -> dict:
    """Curva precision-recall e histograma de score saudável x anômalo —
    Página 3 do frontend (Marco 7). Downsample da curva PR para manter o
    payload pequeno; o histograma usa os mesmos bins para as duas
    populações para permitir sobrepor as barras na interface.
    """
    labels = labels.astype(bool)

    if labels.sum() == 0 or labels.sum() == len(labels):
        pr_curve: list[dict] = []
    else:
        precision, recall, thresholds = precision_recall_curve(labels, scores)
        # precision_recall_curve devolve len(thresholds) == len(precision) - 1
        thresholds = np.append(thresholds, thresholds[-1] if len(thresholds) else 0.0)
        max_points = 50
        idx = np.linspace(0, len(precision) - 1, num=min(max_points, len(precision)), dtype=int)
        pr_curve = [
            {"precision": float(precision[i]), "recall": float(recall[i]), "threshold": float(thresholds[i])}
            for i in idx
        ]

    bin_edges = (
        np.linspace(float(scores.min()), float(scores.max()), n_bins + 1) if len(scores) else np.array([0.0, 1.0])
    )
    healthy_counts, _ = (
        np.histogram(scores[~labels], bins=bin_edges) if (~labels).any() else (np.zeros(n_bins, dtype=int), None)
    )
    anomalous_counts, _ = (
        np.histogram(scores[labels], bins=bin_edges) if labels.any() else (np.zeros(n_bins, dtype=int), None)
    )

    return {
        "pr_curve": pr_curve,
        "score_histogram": {
            "bin_edges": bin_edges.tolist(),
            "healthy": healthy_counts.tolist(),
            "anomalous": anomalous_counts.tolist(),
        },
    }


def detection_delay_windows(predictions: np.ndarray, labels: np.ndarray) -> float:
    """Atraso médio de detecção, em nº de janelas, entre o início de cada
    evento verdadeiro e a primeira janela prevista que o sobrepõe.
    Eventos nunca detectados contam com o atraso máximo possível (a
    duração do próprio evento), para não sumir da média por omissão.
    """
    true_events = _group_into_events(labels.astype(bool))
    if not true_events:
        return float("nan")

    predicted_indices = np.flatnonzero(predictions.astype(bool))
    delays = []
    for start, end in true_events:
        in_event = predicted_indices[(predicted_indices >= start) & (predicted_indices < end)]
        if len(in_event) > 0:
            delays.append(int(in_event.min()) - start)
        else:
            delays.append(end - start)  # nunca detectado dentro do evento
    return float(np.mean(delays))


@dataclass
class EventMetrics:
    n_true_events: int
    n_detected_events: int
    detection_rate: float
    n_false_alarm_events: int
    false_alarms_per_day: float


def _group_into_events(flags: np.ndarray) -> list[tuple[int, int]]:
    """Agrupa uma sequência booleana em blocos contíguos (start, end_exclusive)."""
    events = []
    start = None
    for i, flag in enumerate(flags):
        if flag and start is None:
            start = i
        elif not flag and start is not None:
            events.append((start, i))
            start = None
    if start is not None:
        events.append((start, len(flags)))
    return events


def compute_event_metrics(
    predictions: np.ndarray,
    labels: np.ndarray,
    window_duration_hours: float,
) -> EventMetrics:
    true_events = _group_into_events(labels.astype(bool))
    predicted_events = _group_into_events(predictions.astype(bool))

    detected = 0
    for start, end in true_events:
        true_range = set(range(start, end))
        if any(set(range(p_start, p_end)) & true_range for p_start, p_end in predicted_events):
            detected += 1

    false_alarm_events = 0
    for p_start, p_end in predicted_events:
        pred_range = set(range(p_start, p_end))
        overlaps_true = any(set(range(t_start, t_end)) & pred_range for t_start, t_end in true_events)
        if not overlaps_true:
            false_alarm_events += 1

    total_hours = len(labels) * window_duration_hours
    total_days = total_hours / 24 if total_hours > 0 else 1

    return EventMetrics(
        n_true_events=len(true_events),
        n_detected_events=detected,
        detection_rate=detected / len(true_events) if true_events else float("nan"),
        n_false_alarm_events=false_alarm_events,
        false_alarms_per_day=false_alarm_events / total_days,
    )
