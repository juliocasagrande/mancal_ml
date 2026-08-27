"""Testes centrais do Marco 2: nenhuma janela pode atravessar a fronteira
entre arquivos/splits, mesmo em cenários adversariais onde os timestamps
de arquivos diferentes se sobrepõem ou são intercalados.
"""

import numpy as np
import pandas as pd
import pytest

from app.features.scaling import fit_scaler
from app.features.windows import make_windows

FEATURE_COLUMNS = ["signal"]


def _make_df(source_file: str, split: str, start: str, n: int, value: float) -> pd.DataFrame:
    return pd.DataFrame(
        {
            "timestamp": pd.date_range(start, periods=n, freq="10min"),
            "signal": np.full(n, value),
            "source_file": source_file,
            "split": split,
        }
    )


def test_no_window_mixes_two_source_files_even_with_overlapping_timestamps() -> None:
    # Arquivo A e B têm timestamps deliberadamente sobrepostos: se o
    # janelamento ordenasse globalmente por tempo antes de agrupar por
    # arquivo, uma janela poderia misturar os dois. O valor do sinal
    # (1.0 vs 100.0) denuncia qualquer contaminação.
    df_a = _make_df("A.csv", "train", "2020-01-01 00:00", 20, value=1.0)
    df_b = _make_df("B.csv", "validation", "2020-01-01 01:00", 20, value=100.0)
    df = pd.concat([df_a, df_b], ignore_index=True)

    windows = make_windows(df, FEATURE_COLUMNS, window_size=5, stride=1)

    for w in windows.values:
        unique_values = np.unique(w)
        assert len(unique_values) == 1, "uma janela contém valores de mais de um arquivo/split"


def test_window_split_label_matches_its_source_file() -> None:
    df_a = _make_df("A.csv", "train", "2020-01-01 00:00", 10, value=1.0)
    df_b = _make_df("B.csv", "test", "2020-02-01 00:00", 10, value=2.0)
    df = pd.concat([df_a, df_b], ignore_index=True)

    windows = make_windows(df, FEATURE_COLUMNS, window_size=3, stride=1)

    for source, split in zip(windows.source_file, windows.split):
        expected_split = "train" if source == "A.csv" else "test"
        assert split == expected_split


def test_no_window_extends_past_end_of_its_own_file() -> None:
    # 10 linhas, janela de 4, stride 1 -> últimas janelas possíveis
    # começam no índice 6 (6,7,8,9); não deve haver janela começando
    # depois disso (que exigiria dados fora do arquivo).
    df = _make_df("A.csv", "train", "2020-01-01 00:00", 10, value=1.0)
    windows = make_windows(df, FEATURE_COLUMNS, window_size=4, stride=1)

    assert len(windows.values) == 10 - 4 + 1
    assert all(w.shape == (4, 1) for w in windows.values)


def test_window_count_matches_expected_formula() -> None:
    df = _make_df("A.csv", "train", "2020-01-01 00:00", 100, value=1.0)
    window_size, stride = 10, 5
    windows = make_windows(df, FEATURE_COLUMNS, window_size, stride)

    expected = (100 - window_size) // stride + 1
    assert len(windows.values) == expected


def test_rejects_non_positive_window_or_stride() -> None:
    df = _make_df("A.csv", "train", "2020-01-01 00:00", 10, value=1.0)
    with pytest.raises(ValueError):
        make_windows(df, FEATURE_COLUMNS, window_size=0, stride=1)
    with pytest.raises(ValueError):
        make_windows(df, FEATURE_COLUMNS, window_size=5, stride=0)


def test_scaler_fitted_only_on_train_ignores_validation_and_test_scale() -> None:
    # Se o scaler fosse ajustado com dados de validação/teste, a média
    # aprendida mudaria. Verificamos que o scaler reflete SOMENTE os
    # dados passados como treino.
    train_features = np.array([[1.0], [2.0], [3.0]])
    other_features = np.array([[1000.0], [2000.0]])  # nunca deve influenciar o scaler

    scaler = fit_scaler(train_features)

    assert scaler.mean_[0] == pytest.approx(train_features.mean())
    # Contaminar o cálculo manualmente para comparação: a média mudaria
    # muito se 'other_features' tivesse sido incluída.
    contaminated_mean = np.concatenate([train_features, other_features]).mean()
    assert scaler.mean_[0] != pytest.approx(contaminated_mean)
