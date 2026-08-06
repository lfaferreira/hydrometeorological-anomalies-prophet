import numpy as np
import pandas as pd
import pytest
import xarray as xr

from src.data.preprocess import (
    deaccumulate_precipitation,
    compute_daily_areal_precipitation,
    compute_daily_spatial_stats,
    align_valid_time_to_accumulation_window,
    to_local_time,
)


def test_deaccumulate_precipitation_recovers_hourly_increments():
    times = pd.date_range("2020-01-01 00:00", periods=4, freq="h")
    # acumulado: 1, 3, 6, 2 (reset entre o 3º e o 4º passo)
    cumulative = xr.DataArray([1.0, 3.0, 6.0, 2.0], dims=["valid_time"], coords={"valid_time": times})

    increments = deaccumulate_precipitation(cumulative, time_dim="valid_time")

    # esperado: [1, 2, 3, 2] -> primeiro valor bruto, depois diffs, e o valor bruto no reset
    np.testing.assert_allclose(increments.values, [1.0, 2.0, 3.0, 2.0])


def test_compute_daily_areal_precipitation_matches_known_daily_total(tiny_precip_dataset):
    series = compute_daily_areal_precipitation(tiny_precip_dataset)

    # apos relabel -1h e conversao para America/Recife, os dados de 48h sao repartidos
    # em 3 dias calendarios locais. O primeiro dia (2019-12-31) recebe 4h do ciclo 1 (~4mm).
    assert series.iloc[0] == pytest.approx(4.0, abs=1.0)
    # O segundo dia (2020-01-01) recebe 20h do ciclo 1 (~20mm) + 4h do ciclo 2 (~1.7mm).
    assert series.iloc[1] == pytest.approx(21.67, abs=1.0)


def test_align_valid_time_to_accumulation_window_shifts_back_one_hour():
    times = pd.date_range("2020-01-01 01:00", periods=3, freq="h")
    da = xr.DataArray([1.0, 2.0, 3.0], dims=["valid_time"], coords={"valid_time": times})

    aligned = align_valid_time_to_accumulation_window(da)

    expected_times = pd.date_range("2020-01-01 00:00", periods=3, freq="h")
    np.testing.assert_array_equal(aligned["valid_time"].values, expected_times.values)
    np.testing.assert_allclose(aligned.values, [1.0, 2.0, 3.0])


def test_to_local_time_converts_utc_to_america_recife_fixed_offset():
    times = pd.to_datetime(["2020-01-01T03:00", "2022-06-15T12:00", "2025-12-31T23:00"])
    da = xr.DataArray([1.0, 2.0, 3.0], dims=["valid_time"], coords={"valid_time": times})

    local = to_local_time(da)

    expected = pd.to_datetime(["2020-01-01T00:00", "2022-06-15T09:00", "2025-12-31T20:00"])
    np.testing.assert_array_equal(local["valid_time"].values, expected.values)


def test_compute_daily_areal_precipitation_applies_time_alignment_before_resampling():
    # 26h de dados: passo 00:00 (fim do ciclo anterior, deve ir para o dia anterior
    # apos o relabel -1h) + 24h de um novo ciclo (reset em 01:00) + 1h extra do dia
    # seguinte (fecha o ciclo do dia do meio).
    times = pd.date_range("2020-01-01 00:00", periods=26, freq="h")
    # acumulado (m): [alto = fim do ciclo anterior, reset baixo, sobe 24h, reset de novo]
    cumulative = [0.010] + [0.0002 * i for i in range(1, 24)] + [0.0002 * 24, 0.0001]
    lat, lon = [-8.0, -8.05], [-35.0, -34.95]
    data = np.tile(np.array(cumulative).reshape(26, 1, 1), (1, len(lat), len(lon)))
    ds = xr.Dataset(
        {"tp": (["valid_time", "latitude", "longitude"], data)},
        coords={"valid_time": times, "latitude": lat, "longitude": lon},
    )

    series = compute_daily_areal_precipitation(ds)

    # apos relabel -1h e conversao para America/Recife (-3h), o dia local
    # 2019-12-31 (UTC-3) deve conter o passo bruto 00:00 (fim do ciclo anterior,
    # 10mm) + 3 horas adicionais do proximo ciclo (0.2mm cada)
    assert pd.Timestamp("2019-12-31") in series.index
    assert series.loc[pd.Timestamp("2019-12-31")] == pytest.approx(10.6, abs=0.2)


def test_compute_daily_spatial_stats_returns_mean_max_and_percentiles(tiny_precip_dataset):
    stats = compute_daily_spatial_stats(tiny_precip_dataset)

    assert list(stats.columns) == ["mean", "max", "p90", "p95"]
    # tiny_precip_dataset tem 2 dias UTC, mas o relabel -1h + conversao para
    # America/Recife (-3h) reparte os dados em 3 dias de calendario local
    # (2019-12-31, 2020-01-01, 2020-01-02) -- mesmo comportamento ja coberto
    # por test_compute_daily_areal_precipitation_matches_known_daily_total,
    # que usa o mesmo fixture e checa os 2 primeiros valores dessa mesma serie
    # de 3 pontos.
    assert len(stats) == 3
    # o maximo espacial nunca pode ser menor que a media espacial no mesmo dia
    assert (stats["max"] >= stats["mean"]).all()
    assert (stats["p95"] >= stats["p90"]).all()
    assert (stats["max"] >= stats["p95"]).all()
