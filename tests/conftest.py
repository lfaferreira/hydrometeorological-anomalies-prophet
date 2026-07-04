# tests/conftest.py
import numpy as np
import pandas as pd
import pytest
import xarray as xr


@pytest.fixture
def tiny_precip_dataset() -> xr.Dataset:
    """2 dias, 24 passos horários cada, simulando `tp` acumulado do ERA5-Land (em metros).

    Dia 1: acumulação linear de 0 a 0.024 m (24 mm) ao longo do dia.
    Dia 2: acumulação linear de 0 a 0.010 m (10 mm) ao longo do dia.
    """
    times = pd.date_range("2020-01-01 00:00", periods=48, freq="h")
    day1 = np.linspace(0.001, 0.024, 24)
    day2 = np.linspace(0.0004, 0.010, 24)
    tp = np.concatenate([day1, day2])

    lat = [-8.0, -8.05]
    lon = [-35.0, -34.95]
    data = np.tile(tp.reshape(48, 1, 1), (1, len(lat), len(lon)))

    ds = xr.Dataset(
        {"tp": (["valid_time", "latitude", "longitude"], data)},
        coords={"valid_time": times, "latitude": lat, "longitude": lon},
    )
    return ds


@pytest.fixture
def tiny_prophet_df() -> pd.DataFrame:
    dates = pd.date_range("2020-01-01", periods=100, freq="D")
    rng = np.random.default_rng(0)
    y = 10 + 3 * np.sin(np.arange(100) * 2 * np.pi / 365) + rng.normal(0, 0.5, 100)
    return pd.DataFrame({"ds": dates, "y": y})
