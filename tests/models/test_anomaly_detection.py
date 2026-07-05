import pytest
import pandas as pd

from src.models.anomaly_detection import flag_anomalies


def test_flag_anomalies_marks_points_outside_interval():
    actual = pd.DataFrame({
        "ds": pd.to_datetime(["2022-05-24", "2022-05-25", "2022-05-26"]),
        "y": [20.0, 180.0, 15.0],
    })
    forecast = pd.DataFrame({
        "ds": pd.to_datetime(["2022-05-24", "2022-05-25", "2022-05-26"]),
        "yhat": [18.0, 20.0, 16.0],
        "yhat_lower": [5.0, 5.0, 5.0],
        "yhat_upper": [35.0, 40.0, 30.0],
    })

    result = flag_anomalies(actual, forecast)

    assert result["is_anomaly"].tolist() == [False, True, False]
    # severidade do dia 25: 180 - 40 (yhat_upper) = 140
    row_25 = result.loc[result["ds"] == pd.Timestamp("2022-05-25")].iloc[0]
    assert row_25["severity"] == pytest.approx(140.0)
    row_24 = result.loc[result["ds"] == pd.Timestamp("2022-05-24")].iloc[0]
    assert row_24["severity"] == 0.0
