import pandas as pd
import pytest

from app.features.splits import TEST_FILES, TRAIN_FILES, VALIDATION_FILES, assign_split, file_to_split


def test_split_files_are_mutually_exclusive() -> None:
    all_files = TRAIN_FILES + VALIDATION_FILES + TEST_FILES
    assert len(all_files) == len(set(all_files)), "um arquivo não pode pertencer a mais de um split"


def test_train_is_chronologically_before_validation_and_test() -> None:
    # Junho/Julho (treino) devem preceder Agosto (validação) e
    # Set/Out/Nov (teste) — nunca dividir aleatoriamente séries temporais.
    assert TRAIN_FILES == ["June.csv", "July.csv"]
    assert VALIDATION_FILES == ["Aug.csv"]
    assert TEST_FILES == ["SEP.csv", "Oct.csv", "Nov.csv"]


def test_file_to_split_raises_for_unknown_file() -> None:
    with pytest.raises(ValueError):
        file_to_split("Dec.csv")


def test_assign_split_labels_each_row_correctly() -> None:
    df = pd.DataFrame({"source_file": ["June.csv", "Aug.csv", "Oct.csv"]})
    result = assign_split(df)
    assert list(result["split"]) == ["train", "validation", "test"]


def test_assign_split_raises_on_unknown_source_file() -> None:
    df = pd.DataFrame({"source_file": ["June.csv", "Dec.csv"]})
    with pytest.raises(ValueError):
        assign_split(df)
