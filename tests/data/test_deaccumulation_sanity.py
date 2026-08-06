"""Teste de sanidade (Etapa 2, item 'validar manualmente a de-acumulação'):
reconstrói o total diário de precipitação a partir do NetCDF bruto, com
aritmética independente das funções de `src.data.preprocess`, e compara com
a saída do pipeline para 3 dias amostrais reais (um dia comum, um evento
extremo documentado, um dia seco).

Requer os arquivos NetCDF brutos em dados/raw/ (não versionados no git,
~8.6GB, já presentes neste ambiente de desenvolvimento) — pula
graciosamente se ausentes, para não quebrar uma instalação limpa.
"""

from pathlib import Path

import numpy as np
import pandas as pd
import pytest
import xarray as xr

from src.data.preprocess import compute_daily_areal_precipitation, filter_by_bounding_box

RAW_DIR = Path("dados/raw")
BBOX = {"lat_min": -8.3, "lat_max": -7.9, "lon_min": -35.2, "lon_max": -34.8}

# (arquivo, data, total independente reconstruido manualmente em mm --
# verificado durante o planejamento desta task, ver docs/superpowers/plans/
# 2026-08-06-etapa2-auditar-reconstruir-serie.md)
SAMPLE_DAYS = [
    ("precipitacao_2020_01.nc", "2020-01-02", 1.2388696670532227),
    ("precipitacao_2022_05.nc", "2022-05-25", 16.959760665893555),
    ("precipitacao_2023_08.nc", "2023-08-15", 0.3845314681529999),
]


def _require_raw_file(filename: str) -> Path:
    path = RAW_DIR / filename
    if not path.exists():
        pytest.skip(f"Arquivo bruto {path} ausente — teste de sanidade requer dados/raw/ local")
    return path


def _independent_manual_reconstruction(nc_file: Path, date_str: str) -> float:
    """Reconstrução manual do total diário, sem chamar nenhuma função de
    src.data.preprocess — usada como referência independente."""
    ds = xr.open_dataset(nc_file)
    region = ds.sel(
        latitude=slice(BBOX["lat_max"], BBOX["lat_min"]),
        longitude=slice(BBOX["lon_min"], BBOX["lon_max"]),
    )
    tp_m = region["tp"]

    raw = tp_m.values
    increments = np.empty_like(raw)
    increments[0] = raw[0]
    diffs = raw[1:] - raw[:-1]
    reset = diffs < 0
    increments[1:] = np.where(reset, raw[1:], diffs)
    increments_mm = increments * 1000.0

    times_end_label = pd.DatetimeIndex(tp_m["valid_time"].values)
    times_start_label_utc = times_end_label - pd.Timedelta(hours=1)
    times_local = times_start_label_utc.tz_localize("UTC").tz_convert("America/Recife").tz_localize(None)

    day = pd.Timestamp(date_str)
    day_mask = (times_local >= day) & (times_local < day + pd.Timedelta(days=1))
    assert day_mask.sum() == 24, f"esperado 24 passos horarios para {date_str}, obtido {day_mask.sum()}"

    daily_pixel_total = increments_mm[day_mask].sum(axis=0)
    return float(np.nanmean(daily_pixel_total))


@pytest.mark.parametrize("filename,date_str,expected_mm", SAMPLE_DAYS)
def test_pipeline_matches_independent_manual_reconstruction(filename, date_str, expected_mm):
    nc_path = _require_raw_file(filename)

    # 1. a reconstrucao manual independente bate com o valor verificado no planejamento
    manual_total = _independent_manual_reconstruction(nc_path, date_str)
    assert manual_total == pytest.approx(expected_mm, abs=1e-6)

    # 2. a saida do pipeline real (compute_daily_areal_precipitation) bate com a
    #    reconstrucao manual independente -- validacao cruzada de ponta a ponta
    ds = xr.open_dataset(nc_path)
    region = filter_by_bounding_box(ds, **BBOX)
    series = compute_daily_areal_precipitation(region)

    pipeline_value = float(series.loc[pd.Timestamp(date_str)])
    assert pipeline_value == pytest.approx(expected_mm, abs=1e-4)
