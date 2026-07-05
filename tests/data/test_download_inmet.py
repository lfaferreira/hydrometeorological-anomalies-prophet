import pandas as pd

from src.data.download_inmet import parse_inmet_response


def test_parse_inmet_response_extracts_date_and_rain():
    records = [
        {"DT_MEDICAO": "2022-05-25", "CHUVA": "45.2"},
        {"DT_MEDICAO": "2022-05-26", "CHUVA": None},
        {"DT_MEDICAO": "2022-05-27", "CHUVA": "12.0"},
    ]

    df = parse_inmet_response(records)

    assert list(df.columns) == ["ds", "y"]
    assert df["ds"].dtype.kind == "M"
    assert df.loc[df["ds"] == pd.Timestamp("2022-05-25"), "y"].iloc[0] == 45.2
    # registro nulo deve virar NaN, não quebrar o parsing
    assert pd.isna(df.loc[df["ds"] == pd.Timestamp("2022-05-26"), "y"].iloc[0])
