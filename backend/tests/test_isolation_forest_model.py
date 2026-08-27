import numpy as np

from app.models.isolation_forest_model import IsolationForestModel


def test_fit_and_score_is_deterministic_with_fixed_seed() -> None:
    rng = np.random.default_rng(0)
    train = rng.normal(size=(200, 4))

    model_a = IsolationForestModel(random_state=42).fit(train)
    model_b = IsolationForestModel(random_state=42).fit(train)

    test_point = rng.normal(size=(5, 4))
    np.testing.assert_allclose(model_a.score(test_point), model_b.score(test_point))


def test_outlier_scores_higher_than_inlier() -> None:
    rng = np.random.default_rng(1)
    train = rng.normal(size=(300, 3))
    model = IsolationForestModel(random_state=0).fit(train)

    inlier = np.zeros((1, 3))
    outlier = np.full((1, 3), 50.0)

    assert model.score(outlier)[0] > model.score(inlier)[0]
