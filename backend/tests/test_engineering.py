import numpy as np

from app.features.engineering import compute_window_features


def test_output_shape_matches_number_of_windows_and_statistics() -> None:
    values = np.random.default_rng(0).normal(size=(5, 12, 2))  # 5 janelas, 12 amostras, 2 canais
    derived, names = compute_window_features(values, ["a", "b"])

    n_stats = 6  # mean, std, rms, peak_to_peak, skewness, kurtosis
    assert derived.shape == (5, 2 * n_stats)
    assert len(names) == 2 * n_stats


def test_mean_and_peak_to_peak_are_correct_for_known_input() -> None:
    values = np.array([[[1.0], [2.0], [3.0]]])  # 1 janela, 3 amostras, 1 canal
    derived, names = compute_window_features(values, ["x"])

    mean_idx = names.index("x__mean")
    ptp_idx = names.index("x__peak_to_peak")

    assert derived[0, mean_idx] == 2.0
    assert derived[0, ptp_idx] == 2.0
