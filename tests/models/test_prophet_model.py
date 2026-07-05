import pandas as pd

from src.models.prophet_model import train_test_split_temporal, fit_prophet_model


def test_train_test_split_temporal_splits_by_last_n_days(tiny_prophet_df):
    train, test = train_test_split_temporal(tiny_prophet_df, test_size_days=10)

    assert len(test) == 10
    assert len(train) == len(tiny_prophet_df) - 10
    assert train["ds"].max() < test["ds"].min()


def test_fit_prophet_model_returns_fitted_model(tiny_prophet_df):
    model = fit_prophet_model(tiny_prophet_df, interval_width=0.9)

    forecast = model.predict(tiny_prophet_df[["ds"]])
    assert {"yhat", "yhat_lower", "yhat_upper"}.issubset(forecast.columns)
