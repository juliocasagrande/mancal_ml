import numpy as np

from app.models.baseline import RobustZScoreBaseline


def test_score_is_zero_at_the_median() -> None:
    train = np.array([[1.0], [2.0], [3.0], [4.0], [5.0]])
    baseline = RobustZScoreBaseline().fit(train)

    score = baseline.score(np.array([[3.0]]))  # mediana do treino

    assert score[0] == 0.0


def test_score_increases_with_distance_from_median() -> None:
    train = np.array([[1.0], [2.0], [3.0], [4.0], [5.0]])
    baseline = RobustZScoreBaseline().fit(train)

    near = baseline.score(np.array([[3.5]]))[0]
    far = baseline.score(np.array([[10.0]]))[0]

    assert far > near


def test_constant_feature_in_train_does_not_dominate_score() -> None:
    # Uma coluna constante no treino (MAD=0) não deve mais gerar um
    # z-score astronômico que ofusca as demais colunas (bug corrigido
    # no Marco 3 — ver docs/decisoes).
    train = np.column_stack(
        [
            np.full(10, 5.0),  # constante
            np.linspace(1, 10, 10),  # variável normal
        ]
    )
    baseline = RobustZScoreBaseline().fit(train)

    # pequena variação na coluna constante, grande na variável
    score = baseline.score(np.array([[5.0001, 100.0]]))[0]

    assert score < 1000, "coluna quase constante não deveria dominar o score"


def test_fit_is_based_only_on_train_data() -> None:
    train = np.array([[1.0], [2.0], [3.0]])
    baseline = RobustZScoreBaseline().fit(train)

    assert baseline.median_[0] == 2.0
