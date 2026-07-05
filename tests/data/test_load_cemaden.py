from pathlib import Path

import pandas as pd
import pytest

from src.data.load_cemaden import load_cemaden_csv

FIXTURE = Path(__file__).parent / "fixtures" / "cemaden_sample.csv"


def test_load_cemaden_csv_aggregates_to_daily_total():
    df = load_cemaden_csv(FIXTURE)

    assert list(df.columns) == ["ds", "y"]
    day1 = df.loc[df["ds"] == pd.Timestamp("2022-05-25"), "y"].iloc[0]
    assert day1 == pytest.approx(12.4 + 33.0)
    day2 = df.loc[df["ds"] == pd.Timestamp("2022-05-26"), "y"].iloc[0]
    assert day2 == pytest.approx(5.1)
