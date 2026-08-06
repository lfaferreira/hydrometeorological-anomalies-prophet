"""Processamento de dados de precipitação de arquivos NetCDF para uso no Prophet.

Este módulo carrega múltiplos arquivos NetCDF, filtra uma região de interesse,
agrega espacial e temporalmente os dados e gera um CSV pronto para modelagem
com o Facebook Prophet.
"""

import logging
from pathlib import Path
from typing import Optional

import pandas as pd
import xarray as xr

# Configuração básica de logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def configure_directories(raw_dir: Path, processed_dir: Path) -> None:
    """Garante que os diretórios necessários existam.

    Args:
        raw_dir: Diretório onde estão os arquivos brutos NetCDF.
        processed_dir: Diretório onde os dados processados serão salvos.
    """
    processed_dir.mkdir(parents=True, exist_ok=True)
    logger.info("Diretórios configurados: raw='%s', processed='%s'", raw_dir, processed_dir)


def load_netcdf_data(raw_dir: Path, file_pattern: str = "precipitacao_*.nc") -> xr.Dataset:
    """Carrega múltiplos arquivos NetCDF combinando por coordenadas.

    Args:
        raw_dir: Diretório contendo os arquivos.
        file_pattern: Padrão de nome dos arquivos (curinga '*' permitido).

    Returns:
        Dataset xarray combinado.

    Raises:
        FileNotFoundError: Se nenhum arquivo corresponder ao padrão.
    """
    pattern = raw_dir / file_pattern
    files = sorted(raw_dir.glob(file_pattern))

    if not files:
        raise FileNotFoundError(f"Nenhum arquivo encontrado com o padrão '{pattern}'")

    logger.info("Carregando %d arquivo(s) NetCDF: %s", len(files), [f.name for f in files])
    # Converte para string para evitar problemas de Path com open_mfdataset
    ds = xr.open_mfdataset(str(pattern), combine="by_coords")
    logger.info("Dataset carregado. Dimensões: %s", dict(ds.dims))
    return ds


def filter_by_bounding_box(
    ds: xr.Dataset,
    lat_min: float,
    lat_max: float,
    lon_min: float,
    lon_max: float,
    lat_dim: str = "latitude",
    lon_dim: str = "longitude"
) -> xr.Dataset:
    """Filtra o dataset por uma caixa delimitadora (bounding box).

    Args:
        ds: Dataset xarray com coordenadas de latitude e longitude.
        lat_min: Latitude mínima (sul).
        lat_max: Latitude máxima (norte).
        lon_min: Longitude mínima (oeste).
        lon_max: Longitude máxima (leste).
        lat_dim: Nome da dimensão de latitude.
        lon_dim: Nome da dimensão de longitude.

    Returns:
        Dataset recortado espacialmente.
    """
    logger.info("Filtrando região: lat=[%s, %s], lon=[%s, %s]", lat_min, lat_max, lon_min, lon_max)
    region = ds.sel(
        {lat_dim: slice(lat_max, lat_min), lon_dim: slice(lon_min, lon_max)}
    )
    logger.info("Novas dimensões após filtro: %s", dict(region.dims))
    return region


def deaccumulate_precipitation(da: xr.DataArray, time_dim: str = "valid_time") -> xr.DataArray:
    """Converte uma variável acumulada (ex.: `tp` do ERA5-Land) em incrementos por passo.

    O ERA5-Land acumula `tp` desde o início do ciclo de previsão: cada passo horário
    contém o total acumulado desde o último reset, não o incremento daquela hora.
    Um `diff` negativo entre passos consecutivos indica um reset do acumulador —
    nesse caso o valor bruto do passo já é o incremento correto (reinício da contagem).

    Args:
        da: DataArray com a variável acumulada.
        time_dim: Nome da dimensão temporal.

    Returns:
        DataArray de mesma forma, com o incremento (não acumulado) em cada passo.
    """
    diffed = da.diff(dim=time_dim)
    raw_from_second_step = da.isel({time_dim: slice(1, None)})
    increments = diffed.where(diffed >= 0, raw_from_second_step)
    first_step = da.isel({time_dim: slice(0, 1)})
    return xr.concat([first_step, increments], dim=time_dim)


def align_valid_time_to_accumulation_window(da: xr.DataArray, time_dim: str = "valid_time") -> xr.DataArray:
    """Corrige o rótulo temporal de uma variável acumulada do ERA5-Land.

    O ERA5-Land rotula cada passo horário acumulado com o `valid_time` do
    FINAL da janela de acumulação (convenção ECMWF), não do início. Ex.: o
    valor rotulado `2020-01-02T00:00` é, na verdade, o incremento acumulado
    entre `2020-01-01T23:00` e `2020-01-02T00:00` — ou seja, pertence ao dia
    01/01, não ao dia 02/01. Confirmado empiricamente em
    `dados/raw/precipitacao_2020_01.nc`: para qualquer dia D, o reset do
    acumulador (diff negativo entre passos consecutivos) ocorre no passo
    `D 01:00`, nunca em `D 00:00` — logo `D 00:00` ainda é o último passo
    do ciclo de D-1.

    Sem esta correção, um `resample("1D")` direto sobre `valid_time` inclui
    a última hora do dia ANTERIOR e descarta a última hora do dia CORRENTE
    em cada total diário — um viés sistemático medido em ~10-25% nos dias
    chuvosos amostrados (ver tests/data/test_deaccumulation_sanity.py).

    Args:
        da: DataArray já de-acumulado (ver `deaccumulate_precipitation`),
            com `valid_time` na convenção original do ERA5-Land (rótulo =
            fim da janela).
        time_dim: Nome da dimensão temporal.

    Returns:
        DataArray com `valid_time` deslocado -1h, agora rotulado pelo
        INÍCIO da hora que o valor representa.
    """
    shifted_times = da[time_dim].values - pd.Timedelta(hours=1)
    return da.assign_coords({time_dim: shifted_times})


def to_local_time(da: xr.DataArray, tz: str = "America/Recife", time_dim: str = "valid_time") -> xr.DataArray:
    """Converte o índice temporal (UTC, sem tzinfo) de um DataArray para um fuso local.

    O ERA5-Land reporta `valid_time` em UTC, sem tzinfo explícito. A RMR
    está em `America/Recife` (UTC-3, sem horário de verão desde 2019 — toda
    a janela modelada, 2020-2025, usa o mesmo offset fixo, mas a conversão
    é feita via `zoneinfo`/`tz_convert` em vez de um deslocamento
    hardcoded, para não depender dessa premissa silenciosamente).

    Args:
        da: DataArray com `valid_time` em UTC (naive, sem tzinfo).
        tz: Fuso horário IANA de destino.
        time_dim: Nome da dimensão temporal.

    Returns:
        DataArray com `valid_time` convertido para `tz` e depois com o
        tzinfo removido (mantendo o dtype naive datetime64 exigido por
        `xr.Dataset.resample`), para que o `resample("1D")` subsequente
        agrupe por dia de calendário LOCAL, não UTC.
    """
    localized = (
        pd.DatetimeIndex(da[time_dim].values)
        .tz_localize("UTC")
        .tz_convert(tz)
        .tz_localize(None)
    )
    shifted = da.copy()
    shifted[time_dim] = localized
    return shifted


def _daily_pixel_totals(
    ds: xr.Dataset,
    precip_var: str = "tp",
    time_dim: str = "valid_time",
    scale_factor: float = 1000.0,
) -> xr.DataArray:
    """Prepara o total diário por pixel: escala, de-acumula e alinha o tempo.

    Passos compartilhados por `compute_daily_areal_precipitation` e
    `compute_daily_spatial_stats` — mantidos em uma única função para que
    as duas nunca divirjam na definição de "total diário".

    Args:
        ds: Dataset com variável de precipitação e coordenadas espaciais.
        precip_var: Nome da variável de precipitação.
        time_dim: Nome da dimensão temporal.
        scale_factor: Fator para converter os dados originais para mm.

    Returns:
        DataArray com total diário (calendário local `America/Recife`) por
        pixel, dimensões (`ds`-como-dia, latitude, longitude).
    """
    logger.info("Convertendo '%s' para mm (fator %.1f)", precip_var, scale_factor)
    ds = ds.copy()
    ds[precip_var] = ds[precip_var] * scale_factor

    logger.info("De-acumulando passos horários de '%s'", precip_var)
    ds[precip_var] = deaccumulate_precipitation(ds[precip_var], time_dim=time_dim)

    logger.info("Corrigindo rótulo de janela de acumulação e convertendo para America/Recife")
    aligned_da = align_valid_time_to_accumulation_window(ds[precip_var], time_dim=time_dim)
    ds = ds.assign_coords({time_dim: aligned_da[time_dim]})
    ds[precip_var] = aligned_da

    local_da = to_local_time(ds[precip_var], time_dim=time_dim)
    ds = ds.assign_coords({time_dim: local_da[time_dim]})
    ds[precip_var] = local_da

    logger.info("Agregando temporalmente para total diário (calendário local) por pixel")
    return ds.resample({time_dim: "1D"}).sum(skipna=False)[precip_var]


def compute_daily_areal_precipitation(
    ds: xr.Dataset,
    precip_var: str = "tp",
    time_dim: str = "valid_time",
    scale_factor: float = 1000.0
) -> pd.Series:
    """Calcula a precipitação média diária sobre a área de estudo.

    Passos:
        1. Converte a variável de precipitação para milímetros (fator de escala).
        2. De-acumula os passos horários (ver `deaccumulate_precipitation`).
        3. Corrige o rótulo de janela de acumulação e converte para
           `America/Recife` (ver `align_valid_time_to_accumulation_window`,
           `to_local_time`).
        4. Agrega temporalmente para total diário (calendário local) em cada pixel.
        5. Calcula a média espacial sobre as dimensões lat/lon, ignorando NaNs.

    Args:
        ds: Dataset com variável de precipitação e coordenadas espaciais.
        precip_var: Nome da variável de precipitação.
        time_dim: Nome da dimensão temporal.
        scale_factor: Fator para converter os dados originais para mm.
            (Ex: dados originais em m -> *1000 = mm)

    Returns:
        Série pandas com índice temporal (dias locais) e valores médios
        diários de precipitação (mm).
    """
    daily_pixel = _daily_pixel_totals(ds, precip_var, time_dim, scale_factor)

    logger.info("Calculando média espacial (média de todos os pixels da região)")
    area_mean = daily_pixel.mean(dim=["latitude", "longitude"], skipna=True)

    series = area_mean.to_pandas()
    series = series.dropna()
    logger.info("Série temporal gerada com %d pontos (após remoção de NaNs)", len(series))
    return series


def compute_daily_spatial_stats(
    ds: xr.Dataset,
    precip_var: str = "tp",
    time_dim: str = "valid_time",
    scale_factor: float = 1000.0,
    percentiles: tuple = (0.9, 0.95),
) -> pd.DataFrame:
    """Calcula média, máximo e percentis altos da precipitação diária sobre a área.

    A média areal (usada como `y` do Prophet) atenua extremos localizados —
    esta função complementa com o máximo espacial e percentis altos (p90,
    p95) do dia, que preservam informação sobre picos de chuva concentrados
    em parte da RMR mesmo quando a média do dia é modesta.

    Args:
        ds: Dataset com variável de precipitação e coordenadas espaciais.
        precip_var: Nome da variável de precipitação.
        time_dim: Nome da dimensão temporal.
        scale_factor: Fator para converter os dados originais para mm.
        percentiles: Percentis altos (0-1) a calcular, além de média e máximo.

    Returns:
        DataFrame indexado por dia (local), colunas `mean`, `max`, e uma
        coluna `p{int(q*100)}` por percentil em `percentiles` (ex.: `p90`,
        `p95` para o padrão).
    """
    daily_pixel = _daily_pixel_totals(ds, precip_var, time_dim, scale_factor)

    stats = {
        "mean": daily_pixel.mean(dim=["latitude", "longitude"], skipna=True).to_pandas(),
        "max": daily_pixel.max(dim=["latitude", "longitude"], skipna=True).to_pandas(),
    }
    for q in percentiles:
        label = f"p{int(round(q * 100))}"
        stats[label] = daily_pixel.quantile(q, dim=["latitude", "longitude"], skipna=True).to_pandas()

    df = pd.DataFrame(stats).dropna(how="all")
    logger.info("Estatísticas espaciais diárias geradas com %d linhas", len(df))
    return df


def prepare_prophet_dataframe(series: pd.Series, time_name: str = "ds", value_name: str = "y") -> pd.DataFrame:
    """Converte uma série temporal no formato exigido pelo Facebook Prophet.

    Args:
        series: Série com índice temporal e valores numéricos.
        time_name: Nome da coluna de tempo no DataFrame de saída.
        value_name: Nome da coluna de valores no DataFrame de saída.

    Returns:
        DataFrame com colunas 'ds' (datas) e 'y' (valores).
    """
    df = series.reset_index()
    df.columns = [time_name, value_name]
    logger.info("DataFrame Prophet criado com %d linhas", len(df))
    return df


def save_to_csv(df: pd.DataFrame, output_path: Path) -> None:
    """Salva o DataFrame em um arquivo CSV.

    Args:
        df: DataFrame a ser salvo.
        output_path: Caminho completo do arquivo de saída.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_path, index=False)
    logger.info("Dados salvos com sucesso em: %s", output_path)


def main(
    raw_data_dir: Path = Path("dados/raw"),
    processed_data_dir: Path = Path("dados/processed"),
    metro_area_year: int = 2018,
    file_pattern: str = "precipitacao_*.nc"
) -> Optional[Path]:
    """Pipeline principal de processamento.

    Args:
        raw_data_dir: Diretório com arquivos NetCDF brutos.
        processed_data_dir: Diretório onde os artefatos processados serão salvos.
        metro_area_year: Ano de referência da malha de área metropolitana
            do geobr usada para o polígono da RMR (ver `get_rmr_polygon`).
        file_pattern: Padrão para localizar os arquivos NetCDF.

    Returns:
        Caminho do CSV Prophet (`ds`, `y`) gerado, ou None em caso de erro.
        Também escreve `serie_estatisticas_espaciais_rmr_2020_2025.csv`
        (mean/max/p90/p95) e `metadata.json` no mesmo diretório.
    """
    # imports locais para nao exigir geobr/geopandas em quem so usa as
    # funcoes de agregacao temporal (Tasks 1/3) sem a mascara espacial
    from src.data.metadata import build_processing_metadata, write_metadata
    from src.data.rmr_polygon import get_rmr_polygon, mask_by_polygon

    try:
        configure_directories(raw_data_dir, processed_data_dir)

        raw_files = sorted(raw_data_dir.glob(file_pattern))
        if not raw_files:
            raise FileNotFoundError(f"Nenhum arquivo encontrado com o padrão '{raw_data_dir / file_pattern}'")

        ds_full = load_netcdf_data(raw_data_dir, file_pattern)

        polygon = get_rmr_polygon(year=metro_area_year)
        ds_region = mask_by_polygon(ds_full, polygon)

        precipitation_series = compute_daily_areal_precipitation(ds_region)
        prophet_df = prepare_prophet_dataframe(precipitation_series)

        spatial_stats_df = compute_daily_spatial_stats(ds_region)
        spatial_stats_df.index.name = "ds"

        output_file = processed_data_dir / "serie_prophet_rmr_2020_2025.csv"
        save_to_csv(prophet_df, output_file)

        stats_file = processed_data_dir / "serie_estatisticas_espaciais_rmr_2020_2025.csv"
        spatial_stats_df.reset_index().to_csv(stats_file, index=False)
        logger.info("Estatísticas espaciais salvas em: %s", stats_file)

        minx, miny, maxx, maxy = polygon.bounds
        metadata = build_processing_metadata(
            raw_files=raw_files,
            period_start=str(prophet_df["ds"].min().date()),
            period_end=str(prophet_df["ds"].max().date()),
            spatial_extent={
                "type": "rmr_metro_area_polygon",
                "source": f"geobr.read_metro_area(year={metro_area_year})",
                "name_metro": "Rm Recife",
                "bounds": [minx, miny, maxx, maxy],
            },
        )
        write_metadata(metadata, processed_data_dir / "metadata.json")

        return output_file

    except FileNotFoundError as e:
        logger.error(e)
    except KeyError as e:
        logger.error("Variável ou coordenada ausente no dataset: %s", e)
    except Exception as e:
        logger.exception("Erro inesperado durante o processamento: %s", e)

    return None


if __name__ == "__main__":
    output_path = main()
    if output_path:
        print(f"Sucesso! Arquivo gerado: {output_path}")
    else:
        print("Falha no processamento. Verifique os logs para mais detalhes.")