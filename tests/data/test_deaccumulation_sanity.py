"""Teste de sanidade (Etapa 2, item 'validar manualmente a de-acumulação'):
reconstrói o total diário de precipitação a partir do NetCDF bruto por um
método **estruturalmente diferente** do usado em `src.data.preprocess`, e
compara com a saída do pipeline para 4 dias amostrais reais (um dia comum, os
dois dias do evento extremo documentado de maio/2022, um dia seco).

Por que o método precisa ser diferente, e não só o código
---------------------------------------------------------
A versão anterior deste arquivo reimplementava, com aritmética própria, a
MESMA regra da produção ("diff negativo ⇒ reset ⇒ o incremento é o valor
acumulado bruto"). Era independente em código, mas não em método: não podia,
por construção, detectar um erro na própria regra — e de fato validou um valor
esperado ~10% inflado para 2020-01-02, produzido pelo ruído de arredondamento
do float32 (ver `deaccumulate_precipitation`).

A checagem atual não faz `diff` algum, não detecta reset algum e não itera
sobre as 24 horas do dia: lê 3 valores brutos e os combina. Ver
`_independent_daily_total_from_raw_accumulations`.

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

# (arquivo, data, total diário areal em mm calculado pelo método independente
# de 3 leituras brutas abaixo -- re-derivado nesta etapa; os valores anteriores
# vinham da reconstrução por sinal de diff e estavam contaminados pelo mesmo
# bug da produção. Ver docs/superpowers/plans/
# 2026-08-06-etapa2-auditar-reconstruir-serie.md)
#
# Todos os dias são de meio de mês de propósito: o método precisa dos passos
# brutos de D+1, que para o último dia do mês estariam no arquivo seguinte.
SAMPLE_DAYS = [
    ("precipitacao_2020_01.nc", "2020-01-02", 1.1211087703704834),   # dia comum
    ("precipitacao_2022_05.nc", "2022-05-25", 16.9597606658935547),  # evento extremo documentado
    ("precipitacao_2022_05.nc", "2022-05-28", 85.1344375610351562),  # pico do evento de maio/2022
    ("precipitacao_2023_08.nc", "2023-08-15", 0.3845314681529999),   # dia seco
]


def _require_raw_file(filename: str) -> Path:
    path = RAW_DIR / filename
    if not path.exists():
        pytest.skip(f"Arquivo bruto {path} ausente — teste de sanidade requer dados/raw/ local")
    return path


def _independent_daily_total_from_raw_accumulations(nc_file: Path, date_str: str) -> float:
    """Total diário areal (mm) do dia local `date_str`, lido de 3 valores brutos.

    Não chama nenhuma função de `src.data.preprocess`, não faz `diff`, não
    detecta reset e não soma 24 passos horários — logo não compartilha nem
    código nem método com a de-acumulação de produção.

    Derivação (verificada empiricamente contra `dados/raw/`, ver o relatório
    da etapa):

    1. O acumulador do ERA5-Land reinicia às `01:00 UTC` e cresce
       monotonicamente até o passo `00:00 UTC` do dia seguinte. Portanto o
       valor bruto em um passo `t` JÁ É a soma dos incrementos horários desde
       o início do ciclo — nenhuma reconstrução é necessária.
    2. O `valid_time` rotula o FIM da janela de acumulação; combinado com o
       fuso `America/Recife` (UTC-3), o dia local `D` corresponde exatamente
       aos passos brutos rotulados de `D 04:00 UTC` a `D+1 03:00 UTC`.
    3. Esse intervalo cruza a fronteira de ciclo em `D+1 00:00 / D+1 01:00`.
       Partindo nela:
         - trecho dentro do ciclo de D  (`D 04:00` … `D+1 00:00`)
           = `raw[D+1 00:00] - raw[D 03:00]`   (dois acumulados do mesmo ciclo)
         - trecho no início do ciclo de D+1 (`D+1 01:00` … `D+1 03:00`)
           = `raw[D+1 03:00]`                  (acumulado desde o reset)

    Logo: total(D) = raw[D+1 00:00] - raw[D 03:00] + raw[D+1 03:00].

    (A leitura de um único timestamp, `raw[D+1 00:00]`, daria o total do dia
    UTC, não do dia local — em 2022-05-28 a diferença é de ~4mm, 89.10 vs
    85.13. Os dois termos extras são exatamente a correção de fuso.)
    """
    ds = xr.open_dataset(nc_file)
    region = ds.sel(
        latitude=slice(BBOX["lat_max"], BBOX["lat_min"]),
        longitude=slice(BBOX["lon_min"], BBOX["lon_max"]),
    )
    tp_m = region["tp"]

    day = pd.Timestamp(date_str)

    def raw_at(offset: pd.Timedelta) -> np.ndarray:
        return tp_m.sel(valid_time=day + offset).values

    total_m = (
        raw_at(pd.Timedelta(days=1))                    # fim do ciclo de D
        - raw_at(pd.Timedelta(hours=3))                 # já contabilizado no dia local D-1
        + raw_at(pd.Timedelta(days=1, hours=3))         # primeiras 3h do ciclo de D+1
    )
    return float(np.nanmean(total_m * 1000.0))


@pytest.mark.parametrize("filename,date_str,expected_mm", SAMPLE_DAYS)
def test_pipeline_matches_independent_daily_total(filename, date_str, expected_mm):
    nc_path = _require_raw_file(filename)

    # 1. o metodo independente reproduz o valor re-derivado nesta etapa
    independent_total = _independent_daily_total_from_raw_accumulations(nc_path, date_str)
    assert independent_total == pytest.approx(expected_mm, abs=1e-6)

    # 2. a saida do pipeline real bate com o metodo independente -- validacao
    #    cruzada de ponta a ponta. A tolerancia de 1e-4 mm acomoda o erro de
    #    acumulacao do float32 (maior desvio medido nos 4 dias: 7.6e-6 mm) e
    #    ainda assim reprovaria qualquer erro fisicamente relevante.
    ds = xr.open_dataset(nc_path)
    region = filter_by_bounding_box(ds, **BBOX)
    series = compute_daily_areal_precipitation(region)

    pipeline_value = float(series.loc[pd.Timestamp(date_str)])
    assert pipeline_value == pytest.approx(independent_total, abs=1e-4)


def test_negative_diffs_outside_reset_hour_are_float32_noise():
    """A premissa estrutural do fix da de-acumulação, checada no dado real.

    Se algum dia o ERA5-Land mudar a hora de reset (ou este teste passar a
    rodar sobre outro produto), este teste falha antes que a série seja
    regenerada silenciosamente errada.
    """
    nc_path = _require_raw_file("precipitacao_2022_05.nc")
    ds = xr.open_dataset(nc_path)
    tp = ds.sel(
        latitude=slice(BBOX["lat_max"], BBOX["lat_min"]),
        longitude=slice(BBOX["lon_min"], BBOX["lon_max"]),
    )["tp"]

    raw = tp.values
    hours = pd.DatetimeIndex(tp["valid_time"].values)[1:].hour.values
    diffs = raw[1:] - raw[:-1]
    hour_grid = np.broadcast_to(hours.reshape(-1, 1, 1), diffs.shape)

    off_reset_negative = (diffs < 0) & (hour_grid != 1)
    assert off_reset_negative.any(), "esperado ao menos um diff negativo de ruido fora de 01:00"
    # ruido de arredondamento do float32, nunca um reset (5 ordens de grandeza
    # abaixo de 0.001 mm, o menor valor de chuva fisicamente distinguivel aqui)
    assert float((-diffs[off_reset_negative]).max()) < 1e-7

    # e todo reset genuino (queda grande) esta em 01:00 UTC
    genuine_reset = diffs < -1e-7
    assert genuine_reset.any()
    assert (hour_grid[genuine_reset] == 1).all()
