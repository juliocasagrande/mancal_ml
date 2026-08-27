from pathlib import Path

import pandas as pd

from app.ingestion.loader import load_raw_g1_file
from app.ingestion.schema import RAW_COLUMNS_G1

RAW_HEADER = ",".join(RAW_COLUMNS_G1[:1] + [f"col{i}" for i in range(1, 13)]) + ","


def _write_csv(tmp_path: Path, rows: list[str]) -> Path:
    path = tmp_path / "sample.csv"
    header = RAW_HEADER
    path.write_text(header + "\n" + "\n".join(rows) + "\n", encoding="utf-8")
    return path


def test_drops_malformed_timestamp_and_counts_it(tmp_path: Path) -> None:
    rows = [
        "2020/06/01 00:00:00," + ",".join(["1"] * 12) + ",",
        "NOT-A-DATE," + ",".join(["1"] * 12) + ",",
        "2020/06/01 00:10:00," + ",".join(["1"] * 12) + ",",
    ]
    path = _write_csv(tmp_path, rows)

    df, report = load_raw_g1_file(path)

    assert report.rows_raw == 3
    assert report.rows_dropped_bad_timestamp == 1
    assert report.rows_after_clean == 2
    assert list(df["timestamp"]) == sorted(df["timestamp"])


def test_deduplicates_by_timestamp_keeping_first(tmp_path: Path) -> None:
    rows = [
        "2020/06/01 00:00:00," + ",".join(["1"] * 12) + ",",
        "2020/06/01 00:00:00," + ",".join(["2"] * 12) + ",",
    ]
    path = _write_csv(tmp_path, rows)

    df, report = load_raw_g1_file(path)

    assert report.rows_dropped_duplicate_timestamp == 1
    assert len(df) == 1
    assert df.iloc[0]["generator_power"] == 1


def test_sorts_out_of_order_rows(tmp_path: Path) -> None:
    rows = [
        "2020/06/01 00:20:00," + ",".join(["1"] * 12) + ",",
        "2020/06/01 00:00:00," + ",".join(["1"] * 12) + ",",
        "2020/06/01 00:10:00," + ",".join(["1"] * 12) + ",",
    ]
    path = _write_csv(tmp_path, rows)

    df, _ = load_raw_g1_file(path)

    assert df["timestamp"].is_monotonic_increasing


def test_missing_values_are_flagged_not_imputed(tmp_path: Path) -> None:
    values = ["1"] * 12
    values[3] = ""  # coluna de valor ausente
    rows = ["2020/06/01 00:00:00," + ",".join(values) + ","]
    path = _write_csv(tmp_path, rows)

    df, report = load_raw_g1_file(path)

    assert report.rows_with_missing == 1
    assert df.iloc[0]["has_missing"]
    assert pd.isna(df.iloc[0]["temp_upper_guide_pad1"])
