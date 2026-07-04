import numpy as np
import pandas as pd
import pytest
import xarray as xr

from src.data.preprocess import deaccumulate_precipitation, compute_daily_areal_precipitation


def test_deaccumulate_precipitation_recovers_hourly_increments():
    times = pd.date_range("2020-01-01 00:00", periods=4, freq="h")
    # acumulado: 1, 3, 6, 2 (reset entre o 3º e o 4º passo)
    cumulative = xr.DataArray([1.0, 3.0, 6.0, 2.0], dims=["valid_time"], coords={"valid_time": times})

    increments = deaccumulate_precipitation(cumulative, time_dim="valid_time")

    # esperado: [1, 2, 3, 2] -> primeiro valor bruto, depois diffs, e o valor bruto no reset
    np.testing.assert_allclose(increments.values, [1.0, 2.0, 3.0, 2.0])


def test_compute_daily_areal_precipitation_matches_known_daily_total(tiny_precip_dataset):
    series = compute_daily_areal_precipitation(tiny_precip_dataset)

    # dia 1 deve fechar em ~24mm (0.024m * 1000), dia 2 em ~10mm (0.010m * 1000)
    assert series.iloc[0] == pytest.approx(24.0, abs=1.0)
    assert series.iloc[1] == pytest.approx(10.0, abs=1.0)
