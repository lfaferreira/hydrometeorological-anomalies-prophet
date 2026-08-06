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


def _cumulative_da(start: str, values: list) -> xr.DataArray:
    times = pd.date_range(start, periods=len(values), freq="h")
    return xr.DataArray(values, dims=["valid_time"], coords={"valid_time": times})


def test_deaccumulate_precipitation_recovers_hourly_increments():
    # serie comecando em 01:00 UTC = inicio genuino de um ciclo do ERA5-Land.
    # O 4o passo (04:00) cai 4.76e-8 abaixo do anterior: e o maior |diff|
    # negativo fora de 01:00 medido em toda a serie 2020-2025 -- ruido de
    # arredondamento do float32, nao um reset. Deve virar 0, nunca 6.0.
    cumulative = _cumulative_da("2020-01-01 01:00", [1.0, 3.0, 6.0, 6.0 - 4.76e-8, 8.0])

    increments = deaccumulate_precipitation(cumulative, time_dim="valid_time")

    # primeiro passo (01:00) e o valor bruto; depois diffs, com clip em >= 0
    np.testing.assert_allclose(increments.values, [1.0, 2.0, 3.0, 0.0, 2.0], atol=1e-7)


def test_deaccumulate_precipitation_detects_reset_by_hour_not_by_diff_sign():
    # 01:00 UTC e reset por construcao do ERA5-Land MESMO quando o diff e
    # positivo (80 das 19.728 ocorrencias de 01:00 na serie real). A regra
    # antiga (diff < 0) perdia esses resets silenciosamente.
    cumulative = _cumulative_da("2020-01-01 23:00", [4.0, 4.5, 9.0, 10.0])

    increments = deaccumulate_precipitation(cumulative, time_dim="valid_time")

    # 23:00 -> NaN (primeiro passo fora da hora de reset, ver teste abaixo)
    # 00:00 -> diff = 0.5 (ultimo passo do ciclo)
    # 01:00 -> RESET: valor bruto 9.0, e nao o diff 4.5
    # 02:00 -> diff = 1.0
    np.testing.assert_allclose(increments.values[1:], [0.5, 9.0, 1.0])


def test_deaccumulate_precipitation_marks_ambiguous_first_step_as_nan():
    # a serie real comeca em 2020-01-01 00:00 UTC, que NAO e inicio de ciclo
    # (o ciclo corrente comecou em 2019-12-31 01:00, fora do dado baixado):
    # o incremento daquele passo e desconhecido, nao 4.0.
    ambiguous = _cumulative_da("2020-01-01 00:00", [4.0, 1.0, 2.0])
    assert np.isnan(deaccumulate_precipitation(ambiguous).values[0])

    # ja um primeiro passo em 01:00 e um inicio de ciclo genuino: valor bruto
    genuine = _cumulative_da("2020-01-01 01:00", [4.0, 5.0, 7.0])
    np.testing.assert_allclose(deaccumulate_precipitation(genuine).values, [4.0, 1.0, 2.0])


def test_compute_daily_areal_precipitation_matches_known_daily_total(tiny_precip_dataset):
    series = compute_daily_areal_precipitation(tiny_precip_dataset)

    # apos relabel -1h e conversao para America/Recife (-4h liquido), os 2 ciclos
    # de 24h sao repartidos em 3 dias de calendario local.
    assert list(series.index.strftime("%Y-%m-%d")) == ["2019-12-31", "2020-01-01", "2020-01-02"]
    # 2019-12-31 recebe as 3 primeiras horas do ciclo 1 (1mm/h)
    assert series.iloc[0] == pytest.approx(3.0, abs=1e-6)
    # 2020-01-01 recebe as 21h restantes do ciclo 1 (21mm) + as 3 primeiras do ciclo 2
    assert series.iloc[1] == pytest.approx(22.234783, abs=1e-5)
    # 2020-01-02 recebe as 21h restantes do ciclo 2
    assert series.iloc[2] == pytest.approx(8.765217, abs=1e-5)
    # a de-acumulacao conserva a massa: 24mm (ciclo 1) + 10mm (ciclo 2)
    assert series.sum() == pytest.approx(34.0, abs=1e-6)


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


def _hourly_dataset(start: str, cumulative: list) -> xr.Dataset:
    times = pd.date_range(start, periods=len(cumulative), freq="h")
    lat, lon = [-8.0, -8.05], [-35.0, -34.95]
    data = np.tile(np.array(cumulative).reshape(len(cumulative), 1, 1), (1, len(lat), len(lon)))
    return xr.Dataset(
        {"tp": (["valid_time", "latitude", "longitude"], data)},
        coords={"valid_time": times, "latitude": lat, "longitude": lon},
    )


def test_compute_daily_areal_precipitation_applies_time_alignment_before_resampling():
    # 27h de dados comecando em 01:00 UTC (inicio de ciclo genuino): um ciclo
    # completo de 24h (01:00 -> 00:00 do dia seguinte, 0.2mm/h) + as 3 primeiras
    # horas do ciclo seguinte (0.1mm/h, reset em 01:00).
    cumulative = [0.0002 * i for i in range(1, 25)] + [0.0001, 0.0002, 0.0003]
    ds = _hourly_dataset("2020-01-01 01:00", cumulative)

    series = compute_daily_areal_precipitation(ds)

    # apos relabel -1h e conversao para America/Recife (-3h) = -4h liquido,
    # os passos brutos 01:00-03:00 caem no dia local anterior (2019-12-31)...
    assert pd.Timestamp("2019-12-31") in series.index
    assert series.loc[pd.Timestamp("2019-12-31")] == pytest.approx(0.6, abs=0.01)
    # ...e o dia local 2020-01-01 recebe os 21 passos restantes do 1o ciclo
    # (incluindo o passo bruto 2020-01-02 00:00, que pertence ao ciclo de 01/01)
    # mais as 3 primeiras horas do 2o ciclo: 21*0.2 + 3*0.1
    assert series.loc[pd.Timestamp("2020-01-01")] == pytest.approx(4.5, abs=0.01)


def test_compute_daily_areal_precipitation_drops_ambiguous_first_partial_day():
    # a serie real comeca em 2020-01-01 00:00 UTC, que e a cauda de um ciclo
    # nao observado: o incremento e desconhecido (NaN) e o dia local parcial
    # correspondente nao pode entrar na serie como um "total diario".
    cumulative = [0.010] + [0.0002 * i for i in range(1, 25)] + [0.0001, 0.0002]
    ds = _hourly_dataset("2020-01-01 00:00", cumulative)

    series = compute_daily_areal_precipitation(ds)

    assert pd.Timestamp("2019-12-31") not in series.index
    assert not series.isna().any()
    # o dia local seguinte, completo, sobrevive intacto
    assert series.loc[pd.Timestamp("2020-01-01")] == pytest.approx(4.4, abs=0.01)


def test_compute_daily_spatial_stats_returns_mean_max_and_percentiles(tiny_precip_dataset):
    stats = compute_daily_spatial_stats(tiny_precip_dataset)

    assert list(stats.columns) == ["mean", "max", "p90", "p95"]
    # tiny_precip_dataset tem 2 ciclos de acumulacao (01:00 -> 00:00), mas o relabel -1h + conversao para
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


def test_compute_daily_spatial_stats_with_genuine_spatial_variation():
    # tiny_precip_dataset tiles o MESMO valor em todos os pixels, entao
    # mean == max == p90 == p95 sempre -- nao exercita o caso em que os
    # pixels realmente diferem. Este teste usa 3 pixels com totais diarios
    # diferentes (3mm, 30mm, 4mm) para garantir que max/percentis nao sejam
    # calculados como uma media disfarcada.
    #
    # 3 passos horarios UTC as 01h,02h,03h -- 01:00 e inicio de ciclo do
    # ERA5-Land, entao o primeiro passo e um incremento valido (nao NaN).
    # Apos o relabel -1h e a conversao para America/Recife -3h os tres passos
    # caem no mesmo dia local (2019-12-31 21h-23h), sem se dividirem.
    times = pd.date_range("2020-01-01 01:00", periods=3, freq="h")
    lat = [-8.0]
    lon = [-35.0, -34.95, -34.90]

    # acumulado (m), monotonico (sem reset) por pixel -> total diario = ultimo valor
    pixel_a = [0.001, 0.002, 0.003]  # -> 3mm
    pixel_b = [0.001, 0.002, 0.030]  # -> 30mm (pico concentrado em 1 pixel)
    pixel_c = [0.001, 0.002, 0.004]  # -> 4mm

    data = np.zeros((3, 1, 3))
    data[:, 0, 0] = pixel_a
    data[:, 0, 1] = pixel_b
    data[:, 0, 2] = pixel_c

    ds = xr.Dataset(
        {"tp": (["valid_time", "latitude", "longitude"], data)},
        coords={"valid_time": times, "latitude": lat, "longitude": lon},
    )

    stats = compute_daily_spatial_stats(ds)

    assert len(stats) == 1
    day = stats.iloc[0]
    # media dos 3 pixels: (3 + 30 + 4) / 3
    assert day["mean"] == pytest.approx(12.333, abs=0.01)
    # maximo espacial e o pixel do pico, estritamente maior que a media
    assert day["max"] == pytest.approx(30.0, abs=0.01)
    assert day["max"] > day["mean"]
    # percentis (interpolacao linear sobre [3, 4, 30] ordenado) nao sao
    # forcados a serem iguais por construcao
    assert day["p90"] == pytest.approx(24.8, abs=0.01)
    assert day["p95"] == pytest.approx(27.4, abs=0.01)
    assert day["p95"] > day["p90"]
    assert day["max"] >= day["p95"]
