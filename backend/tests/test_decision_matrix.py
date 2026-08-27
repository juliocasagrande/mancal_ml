from app.evaluation.decision_matrix import compute_decision_matrix


def test_higher_is_better_criterion_favors_larger_value() -> None:
    criteria = {
        "a": {"event_recall": 1.0, "false_alarms_per_day": 1.0, "detection_delay_windows": 1.0,
              "robustness": 0.5, "explainability": 0.5, "latency_p95_ms": 1.0},
        "b": {"event_recall": 0.5, "false_alarms_per_day": 1.0, "detection_delay_windows": 1.0,
              "robustness": 0.5, "explainability": 0.5, "latency_p95_ms": 1.0},
    }
    result = compute_decision_matrix(criteria)
    assert result["a"]["weighted_score"] > result["b"]["weighted_score"]


def test_lower_is_better_criterion_favors_smaller_value() -> None:
    criteria = {
        "a": {"event_recall": 1.0, "false_alarms_per_day": 0.1, "detection_delay_windows": 1.0,
              "robustness": 0.5, "explainability": 0.5, "latency_p95_ms": 1.0},
        "b": {"event_recall": 1.0, "false_alarms_per_day": 10.0, "detection_delay_windows": 1.0,
              "robustness": 0.5, "explainability": 0.5, "latency_p95_ms": 1.0},
    }
    result = compute_decision_matrix(criteria)
    assert result["a"]["weighted_score"] > result["b"]["weighted_score"]


def test_tied_criterion_does_not_distort_ranking() -> None:
    criteria = {
        "a": {"event_recall": 1.0, "false_alarms_per_day": 5.0, "detection_delay_windows": 1.0,
              "robustness": 0.5, "explainability": 0.5, "latency_p95_ms": 1.0},
        "b": {"event_recall": 1.0, "false_alarms_per_day": 5.0, "detection_delay_windows": 1.0,
              "robustness": 0.5, "explainability": 0.5, "latency_p95_ms": 1.0},
    }
    result = compute_decision_matrix(criteria)
    assert result["a"]["weighted_score"] == result["b"]["weighted_score"] == 1.0


def test_breakdown_contains_raw_and_normalized_criteria() -> None:
    criteria = {
        "a": {"event_recall": 1.0, "false_alarms_per_day": 1.0, "detection_delay_windows": 1.0,
              "robustness": 0.5, "explainability": 0.5, "latency_p95_ms": 1.0},
        "b": {"event_recall": 0.2, "false_alarms_per_day": 2.0, "detection_delay_windows": 2.0,
              "robustness": 0.3, "explainability": 0.3, "latency_p95_ms": 2.0},
    }
    result = compute_decision_matrix(criteria)
    assert result["a"]["raw_criteria"]["event_recall"] == 1.0
    assert set(result["a"]["normalized_criteria"].keys()) == set(criteria["a"].keys())
