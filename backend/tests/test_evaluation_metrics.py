import numpy as np

from app.evaluation.labels import build_proxy_labels
from app.evaluation.metrics import compute_event_metrics, compute_window_metrics


def test_proxy_label_flags_low_power_windows() -> None:
    power = np.array([100.0, 5.0, 95.0, 2.0])
    labels = build_proxy_labels(power, train_median_power=100.0)

    assert list(labels) == [False, True, False, True]


def test_window_metrics_perfect_classifier() -> None:
    scores = np.array([0.1, 0.2, 0.9, 0.95])
    labels = np.array([False, False, True, True])

    metrics = compute_window_metrics(scores, labels, threshold=0.5)

    assert metrics.precision == 1.0
    assert metrics.recall == 1.0
    assert metrics.f1 == 1.0
    assert metrics.confusion_matrix == [[2, 0], [0, 2]]


def test_window_metrics_handles_single_class_without_crashing() -> None:
    scores = np.array([0.1, 0.2, 0.3])
    labels = np.array([False, False, False])

    metrics = compute_window_metrics(scores, labels, threshold=0.5)

    assert metrics.precision == 0.0
    assert np.isnan(metrics.pr_auc)


def test_event_metrics_groups_contiguous_windows_into_one_event() -> None:
    # Um único evento verdadeiro contíguo (índices 2-4), detectado por
    # uma janela prevista que se sobrepõe parcialmente a ele.
    labels = np.array([False, False, True, True, True, False, False])
    predictions = np.array([False, False, False, True, False, False, False])

    metrics = compute_event_metrics(predictions, labels, window_duration_hours=1.0)

    assert metrics.n_true_events == 1
    assert metrics.n_detected_events == 1
    assert metrics.detection_rate == 1.0
    assert metrics.n_false_alarm_events == 0


def test_event_metrics_counts_false_alarm_events_separately() -> None:
    labels = np.array([False, False, False, False])
    predictions = np.array([False, True, False, True])

    metrics = compute_event_metrics(predictions, labels, window_duration_hours=1.0)

    assert metrics.n_true_events == 0
    assert metrics.n_false_alarm_events == 2
    assert metrics.false_alarms_per_day == 2 / (4 / 24)
