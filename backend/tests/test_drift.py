import numpy as np

from app.evaluation.drift import classify_psi, compute_drift_report


def test_classify_psi_thresholds() -> None:
    assert classify_psi(0.05) == "none"
    assert classify_psi(0.1) == "moderate"
    assert classify_psi(0.2) == "moderate"
    assert classify_psi(0.25) == "significant"
    assert classify_psi(1.0) == "significant"


def test_identical_distributions_have_near_zero_psi() -> None:
    rng = np.random.default_rng(42)
    reference = rng.normal(size=(500, 2))
    current = rng.normal(size=(500, 2))

    report = compute_drift_report(reference, current, feature_names=["a", "b"])

    assert report.overall_psi < 0.05
    assert report.severity == "none"
    assert report.reference_n == 500
    assert report.current_n == 500


def test_shifted_distribution_is_flagged_significant() -> None:
    rng = np.random.default_rng(42)
    reference = rng.normal(loc=0.0, size=(500, 1))
    current = rng.normal(loc=5.0, size=(200, 1))  # completamente fora do envelope de referência

    report = compute_drift_report(reference, current, feature_names=["a"])

    assert report.severity == "significant"
    assert report.per_feature[0].psi > 0.25


def test_constant_reference_feature_does_not_crash_and_is_marked() -> None:
    reference = np.zeros((100, 1))
    current = np.ones((50, 1)) * 5.0

    report = compute_drift_report(reference, current, feature_names=["dead_channel"])

    assert report.per_feature[0].severity == "constante_no_treino"
    assert report.per_feature[0].psi == 0.0
    assert report.overall_psi == 0.0


def test_multi_feature_report_keeps_per_feature_breakdown() -> None:
    rng = np.random.default_rng(7)
    reference = rng.normal(size=(300, 3))
    current = np.column_stack(
        [
            rng.normal(size=300),  # sem drift
            rng.normal(loc=4.0, size=300),  # drift forte
            rng.normal(size=300),  # sem drift
        ]
    )

    report = compute_drift_report(reference, current, feature_names=["f0", "f1", "f2"])

    assert len(report.per_feature) == 3
    drifted = next(f for f in report.per_feature if f.feature == "f1")
    stable = next(f for f in report.per_feature if f.feature == "f0")
    assert drifted.psi > stable.psi
