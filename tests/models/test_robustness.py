# tests/models/test_robustness.py
import numpy as np
import pandas as pd

from src.models.prophet_model import fit_prophet_model, generate_forecast


def test_pipeline_tolerates_missing_days(tiny_prophet_df):
    rng = np.random.default_rng(1)
    drop_idx = rng.choice(tiny_prophet_df.index, size=10, replace=False)
    df_with_gaps = tiny_prophet_df.drop(index=drop_idx).reset_index(drop=True)

    model = fit_prophet_model(df_with_gaps)
    forecast = generate_forecast(model, tiny_prophet_df[["ds"]])

    # o Prophet deve conseguir prever mesmo para as datas removidas do treino
    assert len(forecast) == len(tiny_prophet_df)
    assert not forecast["yhat"].isna().any()
