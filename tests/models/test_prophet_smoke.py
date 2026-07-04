import numpy as np
import pandas as pd
from prophet import Prophet


def test_prophet_fits_and_forecasts_toy_series():
    dates = pd.date_range("2020-01-01", periods=200, freq="D")
    y = 10 + 3 * np.sin(np.arange(200) * 2 * np.pi / 365) + np.random.default_rng(42).normal(0, 0.5, 200)
    df = pd.DataFrame({"ds": dates, "y": y})

    model = Prophet(interval_width=0.95)
    model.fit(df)
    forecast = model.predict(df)

    assert {"ds", "yhat", "yhat_lower", "yhat_upper"}.issubset(forecast.columns)
    assert len(forecast) == len(df)
    assert (forecast["yhat_lower"] <= forecast["yhat_upper"]).all()
