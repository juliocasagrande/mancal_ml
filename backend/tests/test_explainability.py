import numpy as np

from app.evaluation.explainability import baseline_feature_contribution, lstm_feature_contribution


def test_lstm_contribution_sums_to_one_and_highlights_worst_channel() -> None:
    window = np.zeros((5, 3))
    reconstructed = np.zeros((5, 3))
    reconstructed[:, 1] = 10.0  # canal 1 mal reconstruído

    contribution = lstm_feature_contribution(window, reconstructed, ["a", "b", "c"])

    assert abs(sum(contribution.values()) - 1.0) < 1e-9
    assert contribution["b"] > contribution["a"]
    assert contribution["b"] > contribution["c"]


def test_lstm_contribution_handles_perfect_reconstruction() -> None:
    window = np.random.default_rng(0).normal(size=(4, 2))
    contribution = lstm_feature_contribution(window, window.copy(), ["a", "b"])

    assert contribution == {"a": 0.0, "b": 0.0}


def test_baseline_contribution_highlights_largest_deviation() -> None:
    features = np.array([0.0, 10.0])
    median = np.array([0.0, 0.0])
    mad = np.array([1.0, 1.0])

    contribution = baseline_feature_contribution(features, median, mad, ["x", "y"])

    assert contribution["y"] > contribution["x"]
    assert abs(sum(contribution.values()) - 1.0) < 1e-9
